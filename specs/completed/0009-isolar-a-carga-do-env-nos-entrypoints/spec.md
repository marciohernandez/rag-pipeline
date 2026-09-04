# Especificação integrada: Isolar a carga do .env nos entrypoints

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0009 |
| Slug | 0009-isolar-a-carga-do-env-nos-entrypoints |
| Status | Complete |
| Effort | 3 |
| Effort updated at | 2026-09-03 |
| Effort rationale | Cria um módulo de bootstrap, remove uma chamada do import de `config.py`, toca nove entrypoints da raiz com uma linha cada — três deles trocando uma chamada redundante e um reestruturado para o formato padrão — e adiciona dois testes estáticos de AST mais casos de unidade do bootstrap. Não reescreve lógica de pipeline; a suíte de 255 testes é a prova de regressão. Risco concentrado em não esquecer nenhum entrypoint, mitigado por teste estático. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-03 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

`src/pipeline/config.py` chama `load_dotenv()` no corpo do módulo, na linha 13,
fora de qualquer função. Qualquer import da configuração — um teste, um script
ou a futura camada de aplicação — injeta o `.env` da máquina no processo
inteiro.

O efeito é um acoplamento invisível. Um teste que prova ausência de credencial
passa ou falha conforme qual módulo foi importado antes dele: o teste de
credencial ausente da SPEC-0003 passava isolado e falhava na suíte completa
depois que `OPENAI_API_KEY` foi acrescentada ao `.env` local. O caso foi
blindado com `monkeypatch.delenv`, mas a causa continua.

Além do ruído nos testes, enquanto essa chamada existir a regra de configuração
injetada estabelecida pela SPEC-0008 é contornável: a fachada e os módulos
internos podem ler ambiente que só está presente por causa do efeito colateral
do import. A SPEC-0008 declarou isto como dívida bloqueante da fatia 2 do
BACKLOG-0008 — a implementação do backend de aplicação em `src/app/` — e o
contrato publicado em `docs/architecture.md` registra o impedimento.

#### Resultado desejado

A carga do `.env` deixa de ser efeito colateral de biblioteca e passa a ser
responsabilidade explícita de cada entrypoint da raiz, concentrada em um
bootstrap compartilhado. `src/pipeline/` fica provadamente livre de
`python-dotenv`, verificado por teste estático a cada push. Os testes ficam
determinísticos independentemente do `.env` da máquina e da ordem de import. Os
cinco comandos de operação continuam resolvendo credencial exatamente como
antes, com a mesma invocação. A dívida bloqueante da fatia 2 é encerrada.

#### Métricas de sucesso

- A suíte completa permanece verde com contagem igual ou maior que a baseline
  registrada (255 aprovados) e `uv run ruff check .` sem aviso.
- Zero import de `python-dotenv` ou chamada a `load_dotenv` em qualquer módulo
  sob `src/pipeline/`, verificado por teste estático.
- Os nove entrypoints `.py` da raiz chamam `load_env()` no fluxo de `main()`,
  verificado por teste estático.
- O teste de credencial ausente produz o mesmo resultado executado isolado e
  dentro da suíte completa, com e sem `.env` no disco.
- Os cinco comandos de operação da raiz executam com a mesma invocação de antes.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: qual padrão de fronteira estática já é usado e provado neste
  repositório? → `tests/test_provider_boundaries.py` (SPEC-0003) e
  `tests/test_application_boundaries.py` (SPEC-0008) percorrem a AST de cada
  módulo Python e reprovam import proibido, nomeando arquivo e módulo, com
  exceções explícitas. Esta spec replica o mesmo mecanismo para proibir
  `dotenv` em `src/pipeline/` e para exigir `load_env()` em cada entrypoint da
  raiz.
- **R-002**: onde a carga do `.env` acontece hoje? → `src/pipeline/config.py:11`
  importa `load_dotenv` e `src/pipeline/config.py:13` o chama no corpo do
  módulo. Além disso, `chat.py`, `upsert_from_chunks.py` e `demo_rag.py` já
  chamam `load_dotenv()` no próprio `main()`, de forma redundante com o efeito
  do import.
- **R-003**: quais entrypoints existem na raiz e como consomem configuração? →
  `pipeline.py`, `search.py`, `chat.py`, `validate.py`,
  `upsert_from_chunks.py` (operacionais), mais `main.py`, `demo_rag.py`,
  `inspect_chunks.py` e `quality.py`. `pipeline.py`, `search.py` e `validate.py`
  dependem apenas do efeito colateral do import de `config.py`; os demais já
  carregam `.env` por conta própria ou não resolvem credencial.
- **R-004**: quem lê ambiente para resolver credencial? →
  `src/pipeline/config.py` (`get_openai_api_key`),
  `src/pipeline/providers/embeddings/openai.py`,
  `src/pipeline/providers/vectorstores/qdrant.py` e
  `src/pipeline/providers/vectorstores/pinecone.py`. Essa leitura permanece
  intacta; ela lê variável já presente no ambiente e é responsabilidade dos
  providers, como PR-004 da SPEC-0008 declara.

#### Fontes e contexto consultados

- `specs/inbox/2026-09-02-195708-carregar-o-env-nos-entrypoints-em-vez-do-import-de-config.md`:
  captura de origem, preservada integralmente.
- `specs/backlog/0012-isolar-a-carga-do-env-nos-entrypoints.md`: brief refinado
  com as três decisões confirmadas.
- `specs/completed/0008-fronteira-interna-pipeline-aplicacao/spec.md`: declara a
  dívida como bloqueante da fatia 2 e define PR-004.
- `specs/backlog/0011-contrato-handoff-projeto-mae.md`: registra as duas dívidas
  bloqueantes com rastreio próprio.
- `src/pipeline/config.py`, `pipeline.py`, `search.py`, `chat.py`, `validate.py`,
  `upsert_from_chunks.py`, `main.py`, `demo_rag.py`, `inspect_chunks.py`,
  `quality.py`: superfícies afetadas.
- `tests/test_provider_boundaries.py`, `tests/test_application_boundaries.py`:
  implementação de referência da varredura de AST.
- `docs/architecture.md`, `.specsfy/STACK.md`: destino da atualização documental.

#### Documentação consultada

- Nenhuma documentação externa. Todas as conclusões vêm do código e das specs
  locais.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo. Nenhuma fonte fora do repositório foi consultada,
  portanto não há cópia a preservar em `research/`.

#### Dúvidas respondidas

- **Q**: a carga do `.env` vira responsabilidade de cada CLI ou de um bootstrap
  compartilhado? → **A**: bootstrap compartilhado fora de `src/pipeline/`, com
  uma função chamada por cada entrypoint, e teste estático proibindo `dotenv`
  em `src/pipeline/`.
- **Q**: quais entrypoints passam a chamar a nova função? → **A**: os nove
  `.py` executáveis da raiz, não só os cinco operacionais, para eliminar o
  risco de entrypoint esquecido.
- **Q**: onde fica e como se chama o módulo? → **A**: `src/bootstrap.py`,
  expondo `load_env() -> None`, idempotente e sem sobrescrever variável já
  presente no ambiente.
- **Q**: a resolução de credencial muda? → **A**: não. Continua nos providers e
  em `get_openai_api_key`, lendo ambiente já presente (PR-004 da SPEC-0008).

#### Dúvidas abertas

- Nenhuma.

### 3. Escopo e atores

#### Incluído

- Criar `src/bootstrap.py` com `load_env() -> None`.
- Remover o import e a chamada de `load_dotenv()` de `src/pipeline/config.py`.
- Fazer os nove entrypoints `.py` da raiz chamarem `load_env()` como primeira
  ação do fluxo de `main()`; os três que hoje chamam `load_dotenv()`
  diretamente passam a chamar `load_env()`.
- Reestruturar `inspect_chunks.py` para o formato padrão de entrypoint —
  corpo dentro de `def main()` com bloco `if __name__ == "__main__": main()` —
  sem alterar seu comportamento de inspeção.
- Criar o teste estático que reprova import de `dotenv` ou chamada a
  `load_dotenv` em qualquer módulo sob `src/pipeline/`.
- Criar o teste estático que reprova entrypoint `.py` executável da raiz sem
  `load_env()` no fluxo de `main()`.
- Cobrir por teste de unidade a idempotência de `load_env()`, a não
  sobrescrita de variável presente e a ausência de erro quando `.env` não
  existe.
- Atualizar `docs/architecture.md`, `.specsfy/STACK.md` e `.specsfy/RULES.md`
  para descrever o bootstrap, registrar a regra de que `src/pipeline/` não
  carrega o `.env` e marcar BACKLOG-0012 como resolvida.

#### Fora de escopo

- Implementar `src/app/`, a API FastAPI, execução assíncrona, persistência ou
  qualquer parte da fatia 2 do BACKLOG-0008.
- Mudar a resolução de credencial nos providers ou em `get_openai_api_key`.
- Mudar o contrato de `config.yaml` percebido pelo operador.
- Mudar a invocação, os argumentos ou a saída de qualquer comando da raiz.
- Resolver BACKLOG-0013.
- Substituir `python-dotenv` por outra biblioteca de carga de ambiente.

#### Atores

- **Quem roda a suíte de testes**: precisa que o resultado independa do `.env`
  da máquina e da ordem de import.
- **Operador do pipeline**: Marcio, hoje; executa os comandos da raiz e não
  pode ser interrompido pela mudança.
- **Implementador do backend de aplicação**: escreve `src/app/`; precisa da
  dívida bloqueante encerrada antes de começar.
- **Mantenedor do repositório**: revisa mudanças; precisa que uma regressão da
  fronteira falhe automaticamente, não em leitura de diff.

### 4. Princípios e restrições do projeto

- **PR-001**: a fronteira é verificada por teste estático executado na esteira
  de integração contínua, no mesmo padrão da SPEC-0003 e da SPEC-0008; a
  disciplina não depende de revisão humana.
- **PR-002**: código de biblioteca sob `src/pipeline/` nunca carrega o `.env`;
  apenas lê variáveis já presentes no ambiente.
- **PR-003**: a resolução de credencial permanece nos providers e em
  `get_openai_api_key`, fora de qualquer assinatura pública nova, como PR-004
  da SPEC-0008 declara.
- **PR-004**: os comandos de operação existentes são contrato com o operador;
  esta entrega não altera sua invocação, seus argumentos nem sua saída.
- **PR-005**: `load_env()` não sobrescreve variável já definida no ambiente do
  processo; CI e ambiente real prevalecem sobre o arquivo `.env`.
- **PR-006**: a mudança preserva `python-dotenv` como dependência de carga;
  apenas move o ponto de chamada.

### 5. Histórias de usuário

#### US-001 — Suíte determinística independente do `.env` (P1)

Como pessoa que roda a suíte de testes, quero que o resultado não dependa do
conteúdo do `.env` da máquina nem da ordem de import, para que um teste de
comportamento signifique sempre a mesma coisa.

**Por que P1**: o acoplamento já produziu um falso negativo real na SPEC-0003;
enquanto a causa existir, qualquer teste que dependa de ambiente é frágil.
**Teste independente**: rodar o teste de credencial ausente isolado e dentro da
suíte completa, com e sem `.env` no disco, e obter o mesmo resultado.
**Requisitos**: FR-001, FR-002, FR-004, FR-005

#### US-002 — Operação inalterada (P1)

Como operador do pipeline, quero que os comandos da raiz continuem resolvendo
credencial e funcionando exatamente como hoje, para que a mudança de
carregamento de ambiente não interrompa meu trabalho.

**Por que P1**: a operação é o único uso real do repositório hoje; quebrá-la
troca um problema futuro por um presente.
**Teste independente**: executar cada comando de operação antes e depois da
mudança e comparar invocação, resolução de credencial e saída.
**Requisitos**: FR-003, FR-004

#### US-003 — Fronteira verificável e dívida encerrada (P1)

Como mantenedor do repositório e como implementador do backend, quero que
`src/pipeline/` fique provadamente livre de `dotenv`, que cada entrypoint da
raiz carregue o ambiente e que o contrato esteja documentado, para que a fatia
2 comece sem a dívida bloqueante e a separação sobreviva às próximas entregas.

**Por que P1**: a SPEC-0008 declarou esta dívida como impedimento explícito da
fatia 2; sem verificação automática, ela reaparece.
**Teste independente**: introduzir `import dotenv` em um módulo de
`src/pipeline/` e um entrypoint da raiz sem `load_env()`, e observar a suíte
reprovar identificando arquivo e módulo.
**Requisitos**: FR-002, FR-003, FR-005, FR-006, FR-007

### 6. Cenários BDD de aceite

#### AC-001 — Import de `src/pipeline/` não injeta o `.env`

**Cobre**: US-001, FR-002, FR-005, NFR-004

```gherkin
@US-001 @FR-002 @FR-005 @NFR-004 @AC-001
Feature: Import de biblioteca sem efeito colateral de ambiente

  Scenario: Importar a configuração não lê o .env
    Given nenhum entrypoint da raiz foi executado no processo
    When um teste importa src.pipeline.config ou outro módulo de src/pipeline/
    Then nenhuma variável do arquivo .env é injetada no processo pelo import
    And a decisão de "credencial ausente" não depende de qual módulo foi importado antes
```

#### AC-002 — Comandos de operação resolvem credencial como antes

**Cobre**: US-002, FR-003, NFR-002, NFR-003

```gherkin
@US-002 @FR-003 @NFR-002 @NFR-003 @AC-002
Feature: Preservação da operação

  Scenario: Cada comando da raiz carrega o ambiente e resolve credencial
    Given um arquivo .env válido no diretório de trabalho
    When o operador executa pipeline.py, search.py, chat.py, validate.py ou upsert_from_chunks.py
    Then load_env() é chamado antes da resolução da configuração
    And a credencial é resolvida do .env exatamente como antes da mudança
    And a invocação, os argumentos e a saída de cada comando são idênticos
```

#### AC-003 — Fronteira estática: `src/pipeline/` livre de `dotenv`

**Cobre**: US-003, FR-002, FR-005, NFR-001

```gherkin
@US-003 @FR-002 @FR-005 @NFR-001 @AC-003
Feature: Verificação estática da fronteira de ambiente

  Scenario: Um módulo de src/pipeline/ importa dotenv
    Given um arquivo em src/pipeline/ que importa dotenv ou chama load_dotenv
    When a suíte é executada
    Then o teste estático reprova
    And a mensagem identifica o arquivo e o import proibido
```

#### AC-004 — Cada entrypoint da raiz chama `load_env()`

**Cobre**: US-003, FR-003, FR-006

```gherkin
@US-003 @FR-003 @FR-006 @AC-004
Feature: Cobertura de todos os entrypoints da raiz

  Scenario: Um entrypoint executável da raiz não carrega o ambiente
    Given um arquivo .py na raiz com bloco if __name__ == "__main__" que não chama load_env()
    When a suíte é executada
    Then o teste estático reprova
    And a mensagem identifica o arquivo

  Scenario: inspect_chunks.py conforme ao formato padrão de entrypoint
    Given inspect_chunks.py reestruturado com def main() e bloco if __name__ == "__main__"
    When a suíte é executada
    Then inspect_chunks.py é incluído na varredura de entrypoints
    And chama load_env() no fluxo de main()
    And sua saída de inspeção permanece a mesma de antes
```

#### AC-005 — `load_env()` é idempotente

**Cobre**: US-001, FR-001, FR-004

```gherkin
@US-001 @FR-001 @FR-004 @AC-005
Feature: Bootstrap de ambiente seguro de repetir

  Scenario: Chamar load_env() mais de uma vez
    Given um processo em execução
    When load_env() é chamado duas vezes seguidas
    Then nenhuma exceção é levantada
    And o segundo carregamento não altera o ambiente já resolvido
```

#### AC-006 — Regressão completa

**Cobre**: US-002, US-003, FR-001, FR-006, NFR-001, NFR-003

```gherkin
@US-002 @US-003 @FR-001 @FR-006 @NFR-001 @NFR-003 @AC-006
Feature: Prova de que a mudança não regrediu

  Scenario: Executar suíte, lint e testes estáticos em conjunto
    Given o bootstrap criado e os entrypoints ajustados
    When uv run pytest e uv run ruff check . são executados
    Then todos aprovam
    And o número de testes aprovados não é menor que a baseline registrada de 255
```

#### AC-007 — Um único ponto de carga do `.env`

**Cobre**: US-003, FR-001, FR-003, FR-007

```gherkin
@US-003 @FR-001 @FR-003 @FR-007 @AC-007
Feature: Centralização da carga de ambiente

  Scenario: Nenhum entrypoint chama load_dotenv diretamente
    Given os nove entrypoints da raiz ajustados
    When a suíte inspeciona o texto-fonte de cada um
    Then cada entrypoint carrega o ambiente somente por src.bootstrap.load_env
    And nenhum entrypoint importa dotenv nem chama load_dotenv diretamente
```

#### AC-008 — `.env` ausente não quebra o entrypoint

**Cobre**: US-002, FR-004, NFR-002

```gherkin
@US-002 @FR-004 @NFR-002 @AC-008
Feature: Ausência do arquivo de ambiente

  Scenario: Executar um comando sem .env no diretório
    Given nenhum arquivo .env acessível ao processo
    When um comando da raiz chama load_env()
    Then load_env() não levanta erro
    And a resolução de credencial posterior falha com a mensagem clara já existente quando a credencial faltar
    And nenhum valor de credencial aparece na mensagem
```

#### AC-009 — Variável do ambiente prevalece sobre o `.env`

**Cobre**: US-001, FR-004, NFR-004

```gherkin
@US-001 @FR-004 @NFR-004 @AC-009
Feature: Precedência do ambiente do processo

  Scenario: OPENAI_API_KEY já definida no processo
    Given OPENAI_API_KEY presente no ambiente com um valor
    And um arquivo .env com um valor diferente para a mesma chave
    When load_env() é chamado
    Then o valor já presente no ambiente do processo é preservado
```

#### AC-010 — Contrato documentado em `docs/architecture.md`

**Cobre**: US-003, FR-007, NFR-003

```gherkin
@US-003 @FR-007 @NFR-003 @AC-010
Feature: Contrato publicado e coerente

  Scenario: Consultar a arquitetura depois da mudança
    Given docs/architecture.md publicado
    When alguém consulta a seção de carregamento de configuração e a de dívidas
    Then encontra src/bootstrap.py e load_env como o ponto de carga do .env
    And encontra que os entrypoints da raiz carregam o ambiente
    And a seção de dívidas bloqueantes registra BACKLOG-0012 como resolvida
```

#### AC-011 — Teste de fronteira nomeia arquivo e import

**Cobre**: US-003, FR-005, FR-006, NFR-001

```gherkin
@US-003 @FR-005 @FR-006 @NFR-001 @AC-011
Feature: Mensagem acionável na violação

  Scenario: Violação em qualquer um dos dois sentidos
    Given um módulo de src/pipeline/ que importa dotenv ou um entrypoint da raiz sem load_env()
    When a suíte é executada
    Then o teste estático correspondente reprova
    And a mensagem nomeia o arquivo e, quando houver, o import proibido
    And nenhuma outra ocorrência legítima de dotenv fora de src/pipeline/ é acusada
```

#### AC-012 — Credencial ausente: mesmo resultado isolada e na suíte

**Cobre**: US-001, FR-002, NFR-004

```gherkin
@US-001 @FR-002 @NFR-004 @AC-012
Feature: Determinismo do teste de credencial ausente

  Scenario: Rodar o caso isolado e dentro da suíte completa
    Given um arquivo .env local contendo OPENAI_API_KEY
    And um teste que exige a ausência de credencial
    When o teste roda isolado e depois dentro de uv run pytest
    Then o resultado é o mesmo nas duas execuções
```

#### AC-013 — Contrato de `config.yaml` inalterado

**Cobre**: US-002, NFR-002, NFR-003

```gherkin
@US-002 @NFR-002 @NFR-003 @AC-013
Feature: Preservação do contrato de configuração

  Scenario: Executar um comando com o config.yaml atual
    Given um config.yaml válido no diretório de trabalho
    When o operador executa um comando da raiz após a mudança
    Then as mesmas chaves de configuração são lidas
    And a saída apresentada ao operador é a mesma de antes
```

#### AC-014 — `.specsfy/STACK.md` descreve o bootstrap

**Cobre**: US-003, FR-007, NFR-003

```gherkin
@US-003 @FR-007 @NFR-003 @AC-014
Feature: Contexto técnico coerente com a nova topologia

  Scenario: Consultar a linha de Configuração da stack
    Given .specsfy/STACK.md publicado
    When alguém consulta a linha de Configuração
    Then encontra src/bootstrap.py como o ponto de carga do .env pelos entrypoints
    And não há menção a load_dotenv no import de src/pipeline/config.py
```

#### AC-015 — Regra durável registrada em `.specsfy/RULES.md`

**Cobre**: US-003, FR-002, FR-007

```gherkin
@US-003 @FR-002 @FR-007 @AC-015
Feature: Regra arquitetural preservada para as próximas entregas

  Scenario: Consultar as regras do projeto depois da mudança
    Given .specsfy/RULES.md publicado
    When alguém consulta as regras de configuração e de fronteira
    Then encontra a regra de que módulos sob src/pipeline/ não carregam o .env
    And a carga do .env é responsabilidade dos entrypoints da raiz
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve expor `load_env() -> None` em `src/bootstrap.py`,
  fora de `src/pipeline/` e de `src/app/`. A função carrega o `.env` por
  `python-dotenv`, é idempotente, não sobrescreve variável já presente no
  ambiente do processo e não levanta erro quando o arquivo `.env` não existe.
- **FR-002**: O sistema deve remover o import de `load_dotenv` e sua chamada do
  corpo de `src/pipeline/config.py`, de modo que nenhum módulo sob
  `src/pipeline/` importe `python-dotenv` nem chame `load_dotenv`.
- **FR-003**: O sistema deve fazer cada um dos nove entrypoints `.py` da raiz
  — `pipeline.py`, `search.py`, `chat.py`, `validate.py`,
  `upsert_from_chunks.py`, `main.py`, `demo_rag.py`, `inspect_chunks.py` e
  `quality.py` — chamar `load_env()` como primeira ação do fluxo de `main()`,
  antes de resolver `config.yaml`. Os entrypoints que hoje chamam
  `load_dotenv()` diretamente passam a chamar `load_env()` e deixam de importar
  `dotenv`. `inspect_chunks.py`, que hoje executa código em nível de módulo, é
  reestruturado para o formato padrão — corpo dentro de `def main()` com bloco
  `if __name__ == "__main__": main()` — preservando exatamente sua saída de
  inspeção.
- **FR-004**: O sistema deve manter a resolução de credencial nos providers e
  em `get_openai_api_key` lendo variável já presente no ambiente, sem que a
  ausência de `.env` interrompa o carregamento e sem que `load_env()`
  sobrescreva variável já definida.
- **FR-005**: O sistema deve reprovar, por teste estático de AST executado na
  suíte, qualquer import de `dotenv` ou chamada a `load_dotenv` em módulo sob
  `src/pipeline/`, identificando arquivo e import.
- **FR-006**: O sistema deve reprovar, por teste estático executado na suíte,
  qualquer arquivo `.py` executável da raiz — com bloco
  `if __name__ == "__main__"` — que não chame `load_env()` no fluxo de
  `main()`, identificando o arquivo. Após a reestruturação de
  `inspect_chunks.py` prevista em FR-003, os nove entrypoints da raiz possuem
  esse bloco e são cobertos pelo teste.
- **FR-007**: O sistema deve atualizar `docs/architecture.md`,
  `.specsfy/STACK.md` e `.specsfy/RULES.md` para descrever `src/bootstrap.py` e
  `load_env()` como o ponto de carga do `.env` pelos entrypoints, registrar em
  `.specsfy/RULES.md`, por `$specsfy-aux-rules`, a regra de que módulos sob
  `src/pipeline/` não carregam o `.env`, e marcar BACKLOG-0012 como resolvida
  na seção de dívidas bloqueantes de `docs/architecture.md`.

#### Não funcionais

- **NFR-001**: A mudança não reduz a cobertura existente: a suíte completa
  permanece aprovada com contagem igual ou maior que a baseline de 255 e o
  `ruff check` permanece sem aviso. **Verificação**: `uv run pytest` e
  `uv run ruff check .` antes e depois, com as contagens registradas na
  evidência da tarefa.
- **NFR-002**: Nenhum segredo transita por assinatura nova nem aparece em
  mensagem de erro. `load_env()` não recebe nem devolve credencial.
  **Verificação**: inspeção da assinatura de `load_env()` somada a teste que
  provoca falha de credencial ausente e confere a ausência de valor de
  credencial na mensagem.
- **NFR-003**: A invocação, os argumentos e a saída dos cinco comandos de
  operação da raiz não mudam, e o contrato de `config.yaml` percebido pelo
  operador não muda. **Verificação**: execução de cada comando com `--help` e
  com um `config.yaml` válido, comparada à saída anterior.
- **NFR-004**: O resultado do teste de credencial ausente é determinístico:
  independe da ordem de import dos módulos e da presença do `.env` no disco.
  **Verificação**: execução do caso isolado e dentro da suíte completa, com e
  sem `.env`, comparando o resultado.

#### Erros e casos-limite

- Entrypoint executado sem `.env` no diretório → `load_env()` é no-op; a
  resolução de credencial posterior falha com o erro claro já existente, sem
  regressão e sem expor valor de credencial.
- `load_env()` chamado mais de uma vez no mesmo processo → idempotente, sem
  erro, sem alterar o ambiente já resolvido.
- Variável já definida no ambiente do processo divergente do `.env` →
  `load_env()` preserva o valor do ambiente.
- Novo `.py` executável adicionado à raiz sem `load_env()` → o teste estático
  reprova, nomeando o arquivo.
- Módulo de `src/pipeline/` que volte a importar `dotenv` → o teste estático de
  AST reprova, nomeando arquivo e import.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Aplicação Python 3.12+ gerenciada por `uv`, sem framework web. Testes em
  Pytest (`pyproject.toml` define `testpaths = ["tests"]` e
  `pythonpath = ["."]`), lint com Ruff 0.16.5, esteira GitHub Actions da
  SPEC-0007.
- `src/pipeline/config.py:11` importa `load_dotenv`; a linha 13 o chama no
  corpo do módulo. `chat.py:16,84`, `upsert_from_chunks.py:13,92` e
  `demo_rag.py:21,71` importam e chamam `load_dotenv()` no próprio `main()`.
- `pipeline.py`, `search.py` e `validate.py` não carregam `.env` explicitamente
  e dependem do efeito colateral do import de `config.py`. `inspect_chunks.py`,
  `main.py` e `quality.py` também não carregam `.env` explicitamente.
- A resolução de credencial que lê ambiente está em
  `src/pipeline/config.py:33`, `src/pipeline/providers/embeddings/openai.py:33`,
  `src/pipeline/providers/vectorstores/pinecone.py:146,155` e
  `src/pipeline/providers/vectorstores/qdrant.py:190,200`.
- `tests/test_provider_factory.py:123` e `tests/test_characterization_providers.py:89`
  usam `monkeypatch.delenv("OPENAI_API_KEY")` para se blindar do `.env`.
  `tests/test_pipeline_service.py:121` já exige que a fachada não contenha
  `load_dotenv`.
- A baseline de testes registrada em `docs/architecture.md` após a SPEC-0008 é
  255 aprovados.

#### Arquitetura e módulos

- `src/bootstrap.py`: módulo novo, único responsável por carregar o `.env`.
  Expõe `load_env() -> None`, que delega a `dotenv.load_dotenv()` com o
  comportamento padrão — procura o `.env` a partir do diretório de trabalho,
  não sobrescreve variável já presente. É idempotente por natureza:
  `load_dotenv()` sem `override` não altera variável já definida. Fica fora de
  `src/pipeline/` e de `src/app/` para que CLIs e o futuro backend possam
  importar `from src.bootstrap import load_env` sem cruzar a fronteira da
  SPEC-0008.
- `src/pipeline/config.py`: perde o import `from dotenv import load_dotenv` e a
  chamada `load_dotenv()` da linha 13. O restante — `load_config`,
  `get_openai_api_key`, `setup_logging` — não muda. `get_openai_api_key`
  continua lendo `os.getenv("OPENAI_API_KEY")`.
- Entrypoints da raiz: cada um importa `from src.bootstrap import load_env` e
  chama `load_env()` como primeira linha da função `main()`, antes de qualquer
  `load_config`. `chat.py`, `upsert_from_chunks.py` e `demo_rag.py` trocam
  `from dotenv import load_dotenv` + `load_dotenv()` pela chamada a
  `load_env()`. `inspect_chunks.py` é reestruturado: o bloco de código hoje em
  nível de módulo passa para dentro de `def main()`, com
  `if __name__ == "__main__": main()` no fim; a primeira linha de `main()` é
  `load_env()`. Nenhuma linha de lógica de inspeção muda; apenas o
  aninhamento. `main.py` recebe `load_env()` mesmo sendo um stub, para manter o
  conjunto uniforme.
- `tests/test_env_bootstrap.py`: arquivo novo, modelado sobre
  `tests/test_provider_boundaries.py` e `tests/test_application_boundaries.py`.
  Contém: (a) varredura de AST que reprova import de `dotenv` ou chamada a
  `load_dotenv` em qualquer módulo sob `src/pipeline/`, nomeando arquivo e
  import; (b) varredura dos `.py` da raiz com bloco `if __name__ == "__main__"`
  que reprova ausência de chamada a `load_env()` no fluxo de `main()`, nomeando
  o arquivo; (c) casos de unidade de `load_env()` para idempotência, não
  sobrescrita de variável presente e ausência de erro sem `.env`.

#### Migrations

- Não aplicável. Nenhuma estrutura persistida é tocada. O banco vetorial não é
  acessado.

#### Models

- Não aplicável no sentido de ORM. `load_env()` não tem entrada nem retorno de
  dados; seu efeito é sobre `os.environ` do processo.

#### Controllers e casos de uso

| Caso de uso | Entrada | Saída | Arquivo |
| --- | --- | --- | --- |
| Carregar o `.env` no início de um entrypoint | nenhuma | nenhuma; efeito sobre `os.environ` | `src/bootstrap.py` |

- Autorização não se aplica: é utilitário de processo, não superfície de rede.

#### Views e experiência

- Não aplicável. Sem interface para pessoas. Os comandos de linha de comando
  preservam sua saída atual, sem redesenho.

#### Queries e repositórios

- Não aplicável. O acesso ao banco vetorial não é tocado.

#### Jobs e processamento assíncrono

- Não aplicável. Nenhuma execução assíncrona pertence a esta entrega.

#### Estrutura de arquivos

```text
specs/defined/0009-isolar-a-carga-do-env-nos-entrypoints/
  spec.md
src/
  bootstrap.py            # novo: load_env()
  pipeline/
    config.py             # remove import e chamada de load_dotenv
tests/
  test_env_bootstrap.py   # novo: dois estáticos + unidade de load_env()
pipeline.py               # + load_env() no main()
search.py                 # + load_env() no main()
chat.py                   # troca load_dotenv() por load_env()
validate.py               # + load_env() no main()
upsert_from_chunks.py     # troca load_dotenv() por load_env()
main.py                   # + load_env() no main()
demo_rag.py               # troca load_dotenv() por load_env()
inspect_chunks.py         # reestruturado para main() + __main__; + load_env()
quality.py                # + load_env() no main()
docs/architecture.md      # bootstrap + dívida BACKLOG-0012 resolvida
.specsfy/STACK.md         # linha de Configuração
.specsfy/RULES.md         # regra: src/pipeline/ não carrega o .env
```

### 9. Modelo de dados

#### Entidades

- Não aplicável. A entrega não cria, altera nem persiste entidade. O único
  estado tocado é `os.environ` do processo em execução, transitório por
  natureza.

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Ambiente do processo | sem `.env` carregado | entrypoint chama `load_env()` | `.env` carregado nas chaves ainda ausentes | variável já presente no ambiente não é sobrescrita |
| Ambiente do processo | `.env` já carregado | `load_env()` chamado de novo | inalterado | nenhuma exceção; nenhuma sobrescrita |
| Ambiente do processo | sem `.env` no disco | entrypoint chama `load_env()` | inalterado | nenhuma exceção; resolução de credencial segue lendo o que houver |

#### Migração e retenção

- Não aplicável. Nenhum dado é persistido, migrado ou descartado.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega é um utilitário interno de
  processo consumido por outro código. As únicas superfícies usadas por pessoas
  são os comandos de linha de comando já existentes, cuja invocação e saída
  esta spec preserva sem redesenho.

#### Stack e convenções de interface

- Não aplicável. O repositório não possui camada de interface; `INTERFACE.md`
  registra que nenhuma interface para pessoas está implementada. Esta entrega
  não introduz framework de interface.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável.

#### Menus e navegação principal

- Não aplicável. O operador chega às capacidades pelos comandos de linha de
  comando na raiz, documentados em `docs/application.md`.

#### Formulários e ações

- Não aplicável.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

- Não aplicável. O repositório não usa React.

#### Estados e acessibilidade

- Não aplicável. Sem superfície visual.

#### Contrato CRUD

- Não aplicável. A entrega não expõe CRUD.

#### Revisão visual durante o desenvolvimento

- Não aplicável em todas as tarefas: nenhuma altera superfície visual. Cada
  tarefa registra `VISUAL: Não aplicável` com o motivo concreto.

#### APIs expostas

- Nenhuma. `load_env()` é função de módulo, não rota nem evento.

#### APIs externas utilizadas

- Nenhuma.

#### Documentação das APIs consultadas

- Nenhuma.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: `load_env()` — idempotência, não sobrescrita de variável
  presente, ausência de erro sem `.env`, assinatura sem credencial.
- **Integração/contrato**: dois testes estáticos de AST — `src/pipeline/` sem
  `dotenv` e cada entrypoint da raiz com `load_env()` — modelados sobre
  `tests/test_provider_boundaries.py` e `tests/test_application_boundaries.py`.
- **BDD/aceite**: os cenários AC-001 a AC-014 da seção 6 são o contrato de
  referência que orienta o desenho dos casos TDD. Nenhum arquivo `.feature` é
  criado ou executado.
- **Runner TDD**: Pytest, runner já estabelecido do projeto. Não há PHP nem
  Node; nenhuma decisão nova de runner é necessária.
- **E2E**: Não aplicável no sentido de navegador. A prova de ponta a ponta é a
  execução dos cinco comandos de operação da raiz, com `--help` e com um
  `config.yaml` válido, antes e depois da mudança.
- **Verificação manual**: execução de `--help` dos cinco comandos de operação,
  por serem entrypoints de processo cujo comportamento de invocação não é
  coberto pela suíte. O motivo é registrado na evidência da tarefa.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-002, FR-005, NFR-004, AC-001 | AC-001 na seção 6 | `tests/test_env_bootstrap.py::test_import_de_src_pipeline_nao_injeta_o_env`, marcador `SPECSFY:` próprio | RED 2026-09-03 — importar `src.pipeline.config` em subprocesso injeta a chave exclusiva do `.env`; `stdout` != "" | GREEN 2026-09-03 — subprocesso importa `src.pipeline.config` sem `.env` no processo; `stdout` vazio | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-002, FR-003, NFR-002, NFR-003, AC-002 | AC-002 na seção 6 | `tests/test_env_bootstrap.py::test_entrypoints_operacionais_carregam_ambiente_antes_da_config`, marcador próprio | RED 2026-09-03 — os cinco comandos de operação não chamam `load_env()` | GREEN 2026-09-03 — os cinco comandos chamam `load_env()` antes de `load_config()` | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-003, FR-002, FR-005, NFR-001, AC-003 | AC-003 na seção 6 | `tests/test_env_bootstrap.py::test_src_pipeline_esta_livre_de_dotenv`, marcador próprio | RED 2026-09-03 — `src/pipeline/config.py: from dotenv` e `chamada load_dotenv` | GREEN 2026-09-03 — `dotenv_violations_in_pipeline()` retorna `[]` | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-003, FR-003, FR-006, AC-004 | AC-004 na seção 6 | `tests/test_env_bootstrap.py::test_todo_entrypoint_da_raiz_chama_load_env` e `::test_inspect_chunks_esta_no_formato_padrao_de_entrypoint`, marcador próprio | RED 2026-09-03 — nenhum entrypoint da raiz chama `load_env()`; `inspect_chunks.py` sem `def main()` nem bloco `__main__` | GREEN 2026-09-03 — `entrypoints_sem_load_env()` retorna `[]`; `inspect_chunks.py` com `def main()` + bloco `__main__` | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-001, FR-001, FR-004, AC-005 | AC-005 na seção 6 | `tests/test_env_bootstrap.py::test_load_env_e_idempotente`, marcador próprio | RED 2026-09-03 — `ModuleNotFoundError: No module named 'src.bootstrap'` | GREEN 2026-09-03 — `load_env()` chamado duas vezes sem exceção | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-002, US-003, FR-001, FR-006, NFR-001, NFR-003, AC-006 | AC-006 na seção 6 | `tests/test_ci_gates.py::test_env_bootstrap_module_and_regression_baseline_are_recorded`, marcador próprio | RED 2026-09-03 — a baseline 255 da SPEC-0009 não está declarada em `docs/architecture.md` nem `docs/testing.md` | GREEN 2026-09-03 — `uv run pytest` → 271 passed; `ruff check .` limpo; baseline 255 publicada em `docs/architecture.md` | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-003, FR-001, FR-003, FR-007, AC-007 | AC-007 na seção 6 | `tests/test_env_bootstrap.py::test_carga_do_env_tem_ponto_unico_nos_entrypoints`, marcador próprio | RED 2026-09-03 — nenhum entrypoint importa `src.bootstrap`; `chat.py`, `upsert_from_chunks.py` e `demo_rag.py` referenciam `dotenv` | GREEN 2026-09-03 — os nove entrypoints importam `src.bootstrap.load_env`; nenhum referencia `dotenv` | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-002, FR-004, NFR-002, AC-008 | AC-008 na seção 6 | `tests/test_env_bootstrap.py::test_load_env_sem_arquivo_env_nao_levanta_erro`, marcador próprio | RED 2026-09-03 — `ModuleNotFoundError: No module named 'src.bootstrap'` | GREEN 2026-09-03 — `load_env()` em `tmp_path` sem `.env` retorna `None` | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-001, FR-004, NFR-004, AC-009 | AC-009 na seção 6 | `tests/test_env_bootstrap.py::test_load_env_nao_sobrescreve_variavel_do_ambiente`, marcador próprio | RED 2026-09-03 — `ModuleNotFoundError: No module named 'src.bootstrap'` | GREEN 2026-09-03 — `OPENAI_API_KEY` do ambiente preservada sobre valor divergente no `.env` | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-003, FR-007, NFR-003, AC-010 | AC-010 na seção 6 | `tests/test_docs_safety.py::test_arquitetura_publica_o_bootstrap_do_env_e_encerra_a_divida`, marcador próprio | RED 2026-09-03 — `docs/architecture.md` não cita `src/bootstrap.py` e BACKLOG-0012 ainda consta como bloqueante | GREEN 2026-09-03 — `docs/architecture.md` descreve `src/bootstrap.py`/`load_env` e marca BACKLOG-0012 resolvida | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-003, FR-005, FR-006, NFR-001, AC-011 | AC-011 na seção 6 | `tests/test_env_bootstrap.py::test_scanners_de_fronteira_nomeiam_arquivo_e_import`, marcador próprio | RED 2026-09-03 — `dotenv_violations_in_pipeline()` retorna violações reais em `src/pipeline/config.py` | GREEN 2026-09-03 — violação sintética nomeia arquivo e import; sem falso positivo fora de `src/pipeline/` | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-001, FR-002, NFR-004, AC-012 | AC-012 na seção 6 | `tests/test_env_bootstrap.py::test_teste_de_credencial_ausente_e_deterministico`, marcador próprio | RED 2026-09-03 — com `.env` no cwd o subprocesso imprime `KEY` e sem `.env` imprime `SEM_KEY` | GREEN 2026-09-03 — subprocesso com e sem `.env` no cwd imprime `SEM_KEY` nos dois casos | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-002, NFR-002, NFR-003, AC-013 | AC-013 na seção 6 | `tests/test_env_bootstrap.py::test_contrato_de_config_yaml_inalterado_para_o_operador`, marcador próprio | RED 2026-09-03 — `chat.py` e `upsert_from_chunks.py` ainda importam `dotenv` diretamente | GREEN 2026-09-03 — `--help` código 0 e `--config` presentes; nenhum entrypoint importa `dotenv` | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-003, FR-007, NFR-003, AC-014 | AC-014 na seção 6 | `tests/test_docs_safety.py::test_stack_descreve_o_bootstrap_como_ponto_de_carga_do_env`, marcador próprio | RED 2026-09-03 — `.specsfy/STACK.md` não cita `src/bootstrap.py` | GREEN 2026-09-03 — `.specsfy/STACK.md` cita `src/bootstrap.py` como ponto de carga do `.env` | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |
| US-003, FR-002, FR-007, AC-015 | AC-015 na seção 6 | `tests/test_docs_safety.py::test_rules_registra_que_src_pipeline_nao_carrega_o_env`, marcador próprio | RED 2026-09-03 — `.specsfy/RULES.md` não menciona `src/pipeline/` nem `.env` | GREEN 2026-09-03 — `.specsfy/RULES.md` registra que `src/pipeline/` não carrega o `.env` | Regressão T020: `uv run pytest` → 271 passed; `ruff check .` limpo |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-005 | Unidade | `tests/test_env_bootstrap.py` | Passed — T016 |
| FR-001 | AC-006 | Regressão | `uv run pytest` | Passed — T020 |
| FR-001 | AC-007 | Inspeção | `tests/test_env_bootstrap.py` | Passed — T017 |
| FR-002 | AC-001 | Integração | `tests/test_env_bootstrap.py` | Passed — T017 |
| FR-002 | AC-003 | Contrato | `tests/test_env_bootstrap.py` | Passed — T018 |
| FR-002 | AC-012 | Integração | `tests/test_env_bootstrap.py` | Passed — T017 |
| FR-002 | AC-015 | Inspeção | `tests/test_docs_safety.py` | Passed — T019 |
| FR-003 | AC-002 | Integração | `tests/test_env_bootstrap.py` | Passed — T017 |
| FR-003 | AC-004 | Contrato | `tests/test_env_bootstrap.py` | Passed — T017/T018 |
| FR-003 | AC-007 | Inspeção | `tests/test_env_bootstrap.py` | Passed — T017 |
| FR-004 | AC-005 | Unidade | `tests/test_env_bootstrap.py` | Passed — T016 |
| FR-004 | AC-008 | Unidade | `tests/test_env_bootstrap.py` | Passed — T016 |
| FR-004 | AC-009 | Unidade | `tests/test_env_bootstrap.py` | Passed — T016 |
| FR-005 | AC-001 | Integração | `tests/test_env_bootstrap.py` | Passed — T017 |
| FR-005 | AC-003 | Contrato | `tests/test_env_bootstrap.py` | Passed — T018 |
| FR-005 | AC-011 | Contrato | `tests/test_env_bootstrap.py` | Passed — T018 |
| FR-006 | AC-004 | Contrato | `tests/test_env_bootstrap.py` | Passed — T017/T018 |
| FR-006 | AC-006 | Regressão | `uv run pytest` | Passed — T020 |
| FR-006 | AC-011 | Contrato | `tests/test_env_bootstrap.py` | Passed — T018 |
| FR-007 | AC-007 | Inspeção | `tests/test_env_bootstrap.py` | Passed — T017 |
| FR-007 | AC-010 | Inspeção | `tests/test_docs_safety.py` | Passed — T019 |
| FR-007 | AC-014 | Inspeção | `tests/test_docs_safety.py` | Passed — T019 |
| FR-007 | AC-015 | Inspeção | `tests/test_docs_safety.py` | Passed — T019 |
| NFR-001 | AC-003 | Contrato | `tests/test_env_bootstrap.py` | Passed — T018 |
| NFR-001 | AC-006 | Regressão | `uv run pytest` e `uv run ruff check .` | Passed — T020 |
| NFR-001 | AC-011 | Contrato | `tests/test_env_bootstrap.py` | Passed — T018 |
| NFR-002 | AC-002 | Integração | `tests/test_env_bootstrap.py` | Passed — T017 |
| NFR-002 | AC-008 | Unidade | `tests/test_env_bootstrap.py` | Passed — T016 |
| NFR-002 | AC-013 | Integração | `tests/test_env_bootstrap.py` | Passed — T017 |
| NFR-003 | AC-002 | Integração | `uv run python <entrypoint> --help` | Passed — T017 |
| NFR-003 | AC-006 | Regressão | `uv run pytest` | Passed — T020 |
| NFR-003 | AC-010 | Inspeção | `tests/test_docs_safety.py` | Passed — T019 |
| NFR-003 | AC-013 | Integração | `tests/test_env_bootstrap.py` | Passed — T017 |
| NFR-003 | AC-014 | Inspeção | `tests/test_docs_safety.py` | Passed — T019 |
| NFR-004 | AC-001 | Integração | `tests/test_env_bootstrap.py` | Passed — T017 |
| NFR-004 | AC-009 | Unidade | `tests/test_env_bootstrap.py` | Passed — T016 |
| NFR-004 | AC-012 | Integração | `tests/test_env_bootstrap.py` | Passed — T017 |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY — 2026-09-03 (primeira execução NOT READY na mesma data; reexecutada após as correções)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md` → `VALID`; `node .agents/skills/specsfy-04-validate/scripts/review_findings.mjs specs/draft/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md --root .` → `PASSED` (2 findings, nenhum `P1 Open`).
- **Contagens**: 3 US, 7 FR, 4 NFR, 15 AC, 6 DEC. Cobertura mínima `US/FR/NFR ↔ 3 AC` satisfeita: cada ID tem de 3 a 8 AC em `**Cobre**`.
- **Achados**: dois, ambos `Resolved` na correção de 2026-09-03. A reprovação
  inicial foi semântica, não estrutural.

- **FIND-ARCH-001** [P1] [Resolved] FR-003 e FR-006 eram inconsistentes para `inspect_chunks.py` e `main.py` — Refs: FR-003, FR-006, AC-004, AC-007 — Evidence: inspect_chunks.py — Effect: `inspect_chunks.py` executa código em nível de módulo, sem função `main()` nem bloco `if __name__ == "__main__"`, e `main.py` é um stub de `uv init` sem resolução de configuração; FR-003 exigia `load_env()` "no fluxo de `main()`" e FR-006 verificava pelo bloco `__main__`, então `inspect_chunks.py` não satisfazia nenhum dos dois e AC-004/AC-007 não conseguiam cobri-lo — Suggestion: reestruturar `inspect_chunks.py` para o formato padrão de entrypoint (`def main()` + `__main__`) nesta entrega e manter `main.py` no conjunto de nove com `load_env()`; ajustar FR-003, FR-006, AC-004 e a seção 8. Aplicado em 2026-09-03 pela Pergunta 4 do refinamento do BACKLOG-0012: FR-003, FR-006 e a seção 8 declaram a reestruturação, AC-004 ganhou o cenário de `inspect_chunks.py` incluído na varredura com saída preservada e DEC-006 registra a decisão

- **FIND-PROD-002** [P2] [Resolved] A Definition of Done não exigia registrar a regra nova em `.specsfy/RULES.md` — Refs: PR-002, FR-002, FR-005, FR-007 — Evidence: .specsfy/RULES.md — Effect: a spec confirma uma regra arquitetural durável — "módulos sob `src/pipeline/` nunca carregam o `.env`" (PR-002) — equivalente à regra de fronteira que a SPEC-0008 registrou em `.specsfy/RULES.md`; a seção 18 citava `STACK.md` e `architecture.md`, mas não `RULES.md` — Suggestion: acrescentar à seção 18 um item exigindo o registro da regra em `.specsfy/RULES.md` por `$specsfy-aux-rules`, com AC próprio. Aplicado em 2026-09-03: FR-007 passou a incluir `.specsfy/RULES.md`, AC-015 verifica a regra registrada e a seção 18 ganhou o item de DoD

- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed — 2026-09-03
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md` → `VALID DRAFT` e, após promover o gate, `VALID`.
- **Contagens**: total=20 · tdd=15 (T001–T015) · code=3 (T016–T018) · doc=1 (T019) · test=1 (T020); 29/29 IDs cobertos; 15 predecessores TDD concluídos com RED registrado na seção 11.
- **RED observado**: `uv run pytest` → 255 passed, 16 failed (os 16 casos novos da SPEC-0009 em `tests/test_env_bootstrap.py`, `tests/test_docs_safety.py` e `tests/test_ci_gates.py`), zero regressão na suíte existente; `uv run ruff check .` → `All checks passed!`.
- **Predecessores TDD**: cada tarefa `[CODE]` depende de ao menos três casos TDD com RED; caminho crítico T001..T015 → T016 → T017 → T018 → T019 → T020.
- **Achados**: nenhum bloqueio. `check_traceability.mjs` reporta 29/29 IDs cobertos; o `RESULTADO: GAPS` decorre apenas de marcadores órfãos das SPEC-0001 a SPEC-0007 que compartilham a pasta `tests/`, limitação global já registrada nas specs anteriores. Os identificadores externos foram omitidos desta nota porque o validador estrito os interpreta como declaração desta spec.

#### Gate do Ato III — Entrega

- **Resultado**: Passed — 2026-09-03
- **Aceite final (review → completed)**: READY em 2026-09-03. Reexecutado na pasta `review`: `validate_spec.mjs` → `READY`; `validate_tasks.mjs` → `READY` (20/20 tarefas, 120/120 itens, 29/29 IDs); `review_findings.mjs --root .` → `PASSED` (2 findings, ambos `Resolved`); `verify_acceptance.mjs` → `QA: PASSED`; `verify_evidence.mjs` → `Evidência: PASSED (strict)`; `uv run pytest` → 271 passed; `uv run ruff check .` → `All checks passed!`. Nenhum `BLOCKER` remanescente. Ajuste editorial neste aceite: a nota `IMPROVE` de T020 deixou de citar literalmente o quantificador de quatro letras que dispara `tests/test_spec_markers.py`.
- **Comando**: `uv run pytest` → 271 passed em 21,23s; `uv run ruff check .` → `All checks passed!`; `check_traceability.mjs specs/in-progress/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md .` → 29/29 IDs cobertos, `RESULTADO: GAPS` só por marcadores de specs anteriores; `verify_acceptance.mjs <spec> .` → `QA: PASSED`; `verify_evidence.mjs <spec> .` → `Evidência: PASSED (strict)`; `validate_tasks.mjs <spec>` → `READY` (20/20 tarefas, 120/120 itens); `monitor_context.mjs --project . --check` → `CURRENT`.
- **Achados**: entrega sem bloqueio. Regressão com 271 testes aprovados, acima da baseline mínima de 255 publicada em `docs/architecture.md`. Ruff sem aviso. Rastreabilidade com 29/29 IDs cobertos, `uncovered: []` e `insufficient_cases: {}`; o `RESULTADO: GAPS` decorre exclusivamente de `MARCADORES ÓRFÃOS` das SPEC-0001 a SPEC-0008 que compartilham a pasta `tests/` — nenhum vem de `tests/test_env_bootstrap.py`. A dívida de namespacear marcadores por spec está em `specs/inbox/2026-09-02-195707-namespacear-marcadores-specsfy-por-spec.md`.
- **T016 — bootstrap**: GREEN em 2026-09-03. `src/bootstrap.py` com `load_env() -> None` idempotente e sem `override`; `tests/test_env_bootstrap.py -k "idempotente or sem_arquivo_env or nao_sobrescreve"` → 3 passed; Ruff limpo. Cobertura: US-001, FR-001, FR-004, NFR-002, AC-005, AC-008, AC-009.
- **T017 — remoção do dotenv e nove entrypoints**: GREEN em 2026-09-03. `load_dotenv()` saiu do import de `src/pipeline/config.py`; `pipeline.py`, `search.py`, `validate.py`, `quality.py` e `main.py` chamam `load_env()` na primeira linha de `main()`; `chat.py`, `upsert_from_chunks.py` e `demo_rag.py` trocaram `load_dotenv()` por `load_env()`; `inspect_chunks.py` reestruturado com `def main()` + bloco `__main__`. `tests/test_env_bootstrap.py` → 12 passed; os cinco `--help` → código 0; `uv run pytest` → 271 passed; Ruff limpo. Correção regressiva reversível: `tests/test_pipeline_service.py::test_entrypoints_da_raiz_importam_de_src_pipeline` (SPEC-0008) passou a aceitar `src.bootstrap` como alvo autorizado. Cobertura: US-001, US-002, US-003, FR-002, FR-003, FR-005, FR-006, NFR-001, NFR-002, NFR-003, NFR-004, AC-001, AC-002, AC-004, AC-007, AC-008, AC-011, AC-012, AC-013.
- **T018 — testes estáticos finais**: GREEN em 2026-09-03. As duas varreduras (`dotenv_violations_in_pipeline()` e `entrypoints_sem_load_env()`) já consolidadas na fase RED ficaram verdes com T017, sem código de produção adicional; `tests/test_env_bootstrap.py tests/test_ci_gates.py` → passa. Cobertura: US-003, FR-005, FR-006, NFR-001, AC-003, AC-004, AC-011 e parcela estrutural de AC-006.
- **T019 — documentação**: concluída em 2026-09-03. `docs/architecture.md` descreve `src/bootstrap.py`/`load_env()`, marca `BACKLOG-0012` como resolvido e fixa a baseline mínima em 255; `.specsfy/STACK.md` registra a linha "Carga do `.env`"; `.specsfy/RULES.md` registra a regra de que `src/pipeline/` não carrega o `.env`. `tests/test_docs_safety.py` → 11 passed; monitor `CURRENT`. Cobertura: US-003, FR-002, FR-007, NFR-003, AC-006, AC-007, AC-010, AC-014, AC-015.
- **T020 — regressão e rastreabilidade**: GREEN em 2026-09-03. `uv run pytest` → 271 passed; `uv run ruff check .` limpo; `check_traceability.mjs` → 29/29; `verify_acceptance.mjs` → `QA: PASSED`; `verify_evidence.mjs` → `PASSED (strict)`. Cobertura: todos os US, FR, NFR e AC da spec.

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 o caso de import de `src/pipeline/` sem injeção do `.env` em tests/test_env_bootstrap.py — Refs: US-001, FR-002, FR-005, NFR-004, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 e confirmar que a asserção é sobre `os.environ` após importar `src.pipeline.config` num processo limpo.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `# SPECSFY: US-001 FR-002 FR-005 NFR-004 AC-001`, importando a config em subprocesso ou com `os.environ` restaurado e verificando que uma chave exclusiva do `.env` de fixtura não aparece.
  - [x] **VERIFY**: Observar RED — hoje o import injeta o `.env` e a chave aparece.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando `uv run pytest tests/test_env_bootstrap.py -k import_nao_injeta` e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T002 [TEST] [TDD] [US-002] Derivar do AC-002 o caso de carga e resolução de credencial por entrypoint em tests/test_env_bootstrap.py — Refs: US-002, FR-003, NFR-002, NFR-003, AC-002 — Depends: none
  - [x] **PREP**: Confirmar os cinco comandos de operação e que cada um deve chamar `load_env()` antes de `load_config`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio que faz varredura de texto-fonte dos cinco entrypoints exigindo `load_env(` antes da primeira referência a `load_config(`, e nenhuma mudança de argumentos.
  - [x] **VERIFY**: Observar RED — hoje nenhum dos cinco chama `load_env()`.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T003 [TEST] [TDD] [US-003] Derivar do AC-003 o caso de AST proibindo `dotenv` em `src/pipeline/` em tests/test_env_bootstrap.py — Refs: US-003, FR-002, FR-005, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Ler `tests/test_provider_boundaries.py` como modelo de varredura por AST.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio que percorre a AST de cada módulo sob `src/pipeline/` e reprova `import dotenv`, `from dotenv import ...` ou chamada `load_dotenv`, nomeando arquivo e import.
  - [x] **VERIFY**: Observar RED — `src/pipeline/config.py` importa e chama `load_dotenv` hoje.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T004 [TEST] [TDD] [US-003] Derivar do AC-004 o caso de varredura de `load_env()` nos entrypoints da raiz e da conformidade de `inspect_chunks.py` em tests/test_env_bootstrap.py — Refs: US-003, FR-003, FR-006, AC-004 — Depends: none
  - [x] **PREP**: Confirmar o critério "arquivo `.py` da raiz com bloco `if __name__ == \"__main__\"`" e que `inspect_chunks.py` hoje não o tem.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio que reprova entrypoint da raiz sem `load_env()` no fluxo de `main()`, com um cenário adicional exigindo `inspect_chunks.py` já no formato padrão e com a mesma saída de inspeção.
  - [x] **VERIFY**: Observar RED — nenhum entrypoint chama `load_env()` e `inspect_chunks.py` roda em nível de módulo.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 o caso de idempotência de `load_env()` em tests/test_env_bootstrap.py — Refs: US-001, FR-001, FR-004, AC-005 — Depends: none
  - [x] **PREP**: Definir a expectativa: duas chamadas seguidas sem exceção e sem alterar o ambiente já resolvido.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio que importa `from src.bootstrap import load_env` e chama `load_env()` duas vezes com `monkeypatch.chdir(tmp_path)`.
  - [x] **VERIFY**: Observar RED — `ModuleNotFoundError: No module named 'src.bootstrap'`.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 o caso de coletabilidade dos testes estáticos e da baseline de regressão registrada em tests/test_ci_gates.py — Refs: US-002, US-003, FR-001, FR-006, NFR-001, NFR-003, AC-006 — Depends: none
  - [x] **PREP**: Confirmar a baseline mínima 255 já publicada em `docs/architecture.md` pela SPEC-0008 e o módulo `tests/test_env_bootstrap.py` como alvo coletável.
  - [x] **EXECUTE**: Acrescentar caso com marcador próprio que importa `tests/test_env_bootstrap.py`, confirma as duas funções de fronteira estática e verifica a baseline documentada de 255.
  - [x] **VERIFY**: Observar RED — `tests/test_env_bootstrap.py` ainda não existe.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T007 [TEST] [TDD] [US-003] Derivar do AC-007 o caso de ponto único de carga do `.env` nos entrypoints em tests/test_env_bootstrap.py — Refs: US-003, FR-001, FR-003, FR-007, AC-007 — Depends: none
  - [x] **PREP**: Listar os nove entrypoints e definir a asserção: cada um importa `src.bootstrap.load_env` e nenhum importa `dotenv` nem chama `load_dotenv`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio que inspeciona o texto-fonte dos nove arquivos.
  - [x] **VERIFY**: Observar RED — três entrypoints ainda chamam `load_dotenv()` diretamente e nenhum importa `src.bootstrap`.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 o caso de `.env` ausente sem quebra do entrypoint em tests/test_env_bootstrap.py — Refs: US-002, FR-004, NFR-002, AC-008 — Depends: none
  - [x] **PREP**: Definir a expectativa: `load_env()` em diretório sem `.env` não levanta erro; mensagem de credencial ausente permanece sem valor de credencial.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio usando `monkeypatch.chdir(tmp_path)` sem `.env` e conferindo que `load_env()` retorna sem exceção.
  - [x] **VERIFY**: Observar RED — `ModuleNotFoundError: No module named 'src.bootstrap'`.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T009 [TEST] [TDD] [US-001] Derivar do AC-009 o caso de precedência da variável do ambiente sobre o `.env` em tests/test_env_bootstrap.py — Refs: US-001, FR-004, NFR-004, AC-009 — Depends: none
  - [x] **PREP**: Definir a expectativa: `OPENAI_API_KEY` já no ambiente prevalece sobre valor divergente no `.env`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio que faz `monkeypatch.setenv` da chave, grava um `.env` com outro valor em `tmp_path`, chama `load_env()` e confere o valor do ambiente preservado.
  - [x] **VERIFY**: Observar RED — `ModuleNotFoundError: No module named 'src.bootstrap'`.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-010 o caso de contrato do bootstrap em docs/architecture.md em tests/test_docs_safety.py — Refs: US-003, FR-007, NFR-003, AC-010 — Depends: none
  - [x] **PREP**: Confirmar os itens verificáveis por texto: `src/bootstrap.py`, `load_env`, entrypoints carregando o ambiente, BACKLOG-0012 resolvida.
  - [x] **EXECUTE**: Acrescentar caso com marcador próprio que lê `docs/architecture.md` e exige esses itens.
  - [x] **VERIFY**: Observar RED — `docs/architecture.md` não cita `src/bootstrap.py` e a dívida ainda consta como bloqueante.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 o caso de mensagem acionável do teste de fronteira nos dois sentidos em tests/test_env_bootstrap.py — Refs: US-003, FR-005, FR-006, NFR-001, AC-011 — Depends: none
  - [x] **PREP**: Definir a expectativa: violação em `src/pipeline/` ou em entrypoint da raiz produz mensagem com o arquivo e, quando houver, o import; ocorrência legítima de `dotenv` fora de `src/pipeline/` não é acusada.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio que injeta um módulo de fixtura violando cada sentido e confere o texto da falha.
  - [x] **VERIFY**: Observar RED — as funções de varredura ainda não existem.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T012 [TEST] [TDD] [US-001] Derivar do AC-012 o caso de determinismo do teste de credencial ausente em tests/test_env_bootstrap.py — Refs: US-001, FR-002, NFR-004, AC-012 — Depends: none
  - [x] **PREP**: Confirmar que o alvo é a estabilidade do resultado com e sem `.env` e independente da ordem de import.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio que executa a lógica de credencial ausente com um `.env` de fixtura presente e ausente, exigindo o mesmo desfecho.
  - [x] **VERIFY**: Observar RED — hoje o import de `config.py` injeta o `.env` e o desfecho muda.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T013 [TEST] [TDD] [US-002] Derivar do AC-013 o caso de contrato de config.yaml inalterado para o operador em tests/test_env_bootstrap.py — Refs: US-002, NFR-002, NFR-003, AC-013 — Depends: none
  - [x] **PREP**: Definir a asserção: os cinco comandos leem as mesmas chaves de `config.yaml` e produzem a mesma saída após a mudança.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio que executa cada comando com `--help` e com um `config.yaml` de fixtura mínimo, comparando código de saída e chaves lidas.
  - [x] **VERIFY**: Observar RED — o caso ainda não existe e a suíte não cobre a invocação dos entrypoints.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T014 [TEST] [TDD] [US-003] Derivar do AC-014 o caso de descrição do bootstrap na linha de Configuração de .specsfy/STACK.md em tests/test_docs_safety.py — Refs: US-003, FR-007, NFR-003, AC-014 — Depends: none
  - [x] **PREP**: Confirmar os itens verificáveis: `src/bootstrap.py` como ponto de carga do `.env` pelos entrypoints; ausência de menção a `load_dotenv` no import de `src/pipeline/config.py`.
  - [x] **EXECUTE**: Acrescentar caso com marcador próprio que lê `.specsfy/STACK.md` e exige esses itens.
  - [x] **VERIFY**: Observar RED — a linha de Configuração ainda descreve `python-dotenv` em `src/pipeline/config.py`.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

- [x] T015 [TEST] [TDD] [US-003] Derivar do AC-015 o caso de regra durável registrada em .specsfy/RULES.md em tests/test_docs_safety.py — Refs: US-003, FR-002, FR-007, AC-015 — Depends: none
  - [x] **PREP**: Confirmar o texto verificável: módulos sob `src/pipeline/` não carregam o `.env`; a carga é responsabilidade dos entrypoints da raiz.
  - [x] **EXECUTE**: Acrescentar caso com marcador próprio que lê `.specsfy/RULES.md` e exige a regra.
  - [x] **VERIFY**: Observar RED — `.specsfy/RULES.md` não registra a regra.
  - [x] **VISUAL**: `Não aplicável` — tarefa de teste.
  - [x] **EVIDENCE**: Registrar comando e a causa do RED na seção 11.
  - [x] **IMPROVE**: Registrar melhoria de cobertura ou ausência justificada.

#### Fase 2 — US-001 Suíte determinística independente do `.env` (P1)

**Objetivo**: `src/bootstrap.py` com `load_env()` e a config sem efeito colateral de ambiente.
**Teste independente**: `uv run pytest tests/test_env_bootstrap.py` cobre idempotência, `.env` ausente e precedência do ambiente.

- [x] T016 [CODE] [US-001] Criar src/bootstrap.py com load_env() -> None idempotente e sem override — Refs: US-001, FR-001, FR-004, NFR-002, AC-005, AC-008, AC-009 — Depends: T005, T008, T009
  - [x] **PREP**: Confirmar RED de T005, T008 e T009 por `ModuleNotFoundError: No module named 'src.bootstrap'`; reconstruir `docs/` por `$specsfy-documentator` e conferir monitor `CURRENT` antes de `EXECUTE`.
  - [x] **EXECUTE**: Criar `src/bootstrap.py` com `load_env() -> None` delegando a `dotenv.load_dotenv()` no comportamento padrão (sem `override`), sem parâmetros e sem retorno de credencial.
  - [x] **VERIFY**: `uv run pytest tests/test_env_bootstrap.py -k "idempotente or sem_arquivo_env or nao_sobrescreve"` → 3 passed; `uv run ruff check src/bootstrap.py` → `All checks passed!`.
  - [x] **VISUAL**: `Não aplicável` — módulo utilitário de processo, sem superfície visual.
  - [x] **EVIDENCE**: GREEN de T005/T008/T009 registrado na seção 11; `src/bootstrap.py` criado com `load_env() -> None` delegando a `dotenv.load_dotenv()` sem `override`.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária — o módulo é mínimo por desenho (uma função, uma linha efetiva); a docstring já registra as três garantias (idempotência, não sobrescrita, ausência de erro sem `.env`).
  <!-- specsfy:evidence {"task":"T016","refs":["US-001","FR-001","FR-004","NFR-002","AC-005","AC-008","AC-009"],"files":["src/bootstrap.py"],"commands":[{"run":"uv run pytest tests/test_env_bootstrap.py -k 'idempotente or env_ausente or precedencia'","exit":0},{"run":"uv run ruff check src/bootstrap.py","exit":0}]} -->

#### Fase 3 — US-002 Operação inalterada (P1)

**Objetivo**: `config.py` sem `load_dotenv()` e os nove entrypoints carregando o ambiente sem mudar sua invocação.
**Teste independente**: os cinco comandos respondem a `--help` com código 0 e resolvem credencial como antes.

- [x] T017 [CODE] [US-002] Remover load_dotenv() de src/pipeline/config.py e fazer os nove entrypoints da raiz chamarem load_env() no main(), reestruturando inspect_chunks.py e trocando a chamada redundante em chat.py, upsert_from_chunks.py e demo_rag.py — Refs: US-001, US-002, US-003, FR-002, FR-003, FR-005, FR-006, NFR-001, NFR-002, NFR-003, NFR-004, AC-001, AC-002, AC-004, AC-007, AC-008, AC-011, AC-012, AC-013 — Depends: T001, T002, T003, T004, T007, T008, T011, T012, T013, T016
  - [x] **PREP**: Confirmar RED de T001, T002, T003, T004, T007, T011, T012 e T013; inventariar por `rg` os pontos de import de `dotenv` e as chamadas `load_dotenv`; reconstruir `docs/` por `$specsfy-documentator` e conferir monitor `CURRENT`.
  - [x] **EXECUTE**: Remover `from dotenv import load_dotenv` e `load_dotenv()` de `src/pipeline/config.py`; em `pipeline.py`, `search.py`, `validate.py`, `quality.py` e `main.py` adicionar `from src.bootstrap import load_env` e `load_env()` como primeira linha de `main()`; em `chat.py`, `upsert_from_chunks.py` e `demo_rag.py` trocar `from dotenv import load_dotenv` + `load_dotenv()` por `load_env()`; em `inspect_chunks.py` mover o corpo para `def main()` com `if __name__ == "__main__": main()` e `load_env()` na primeira linha, sem alterar a lógica de inspeção.
  - [x] **VERIFY**: `uv run pytest tests/test_env_bootstrap.py` → 12 passed; `uv run python <entrypoint> --help` → código 0 para `pipeline.py`, `search.py`, `chat.py`, `validate.py` e `upsert_from_chunks.py`; `uv run python inspect_chunks.py` → mesmo `FileNotFoundError` de antes (o diretório `arquivos processados` é local do desenvolvedor); `uv run pytest` → 271 passed, `uv run ruff check .` → `All checks passed!`. Correção regressiva: `tests/test_pipeline_service.py::test_entrypoints_da_raiz_importam_de_src_pipeline` (SPEC-0008) passou a aceitar `src.bootstrap` como alvo autorizado.
  - [x] **VISUAL**: `Não aplicável` — nenhum arquivo altera superfície visual; os CLIs preservam saída atual.
  - [x] **EVIDENCE**: GREEN de T001/T002/T003/T004/T007/T011/T012/T013 registrado na seção 11; `PROJECT.md` conferido — a mudança é interna (ponto de carga do `.env`) e não altera história, finalidade, capacidades nem limites; monitor `CURRENT` com `--acknowledge-project-no-change`.
  - [x] **IMPROVE**: A migração atômica funcionou porque os pontos de `dotenv` foram inventariados por `grep` antes da edição e a suíte de 255 testes serviu de rede imediata; `load_env()` ficou como primeira linha real de `main()` em todos os nove entrypoints.
  <!-- specsfy:evidence {"task":"T017","refs":["US-001","US-002","US-003","FR-002","FR-003","FR-005","FR-006","NFR-001","NFR-002","NFR-003","NFR-004","AC-001","AC-002","AC-004","AC-007","AC-008","AC-011","AC-012","AC-013"],"files":["src/pipeline/config.py","pipeline.py","search.py","chat.py","validate.py","upsert_from_chunks.py","main.py","demo_rag.py","inspect_chunks.py","quality.py"],"commands":[{"run":"uv run pytest tests/test_env_bootstrap.py","exit":0},{"run":"uv run pytest","exit":0},{"run":"uv run ruff check .","exit":0}]} -->

#### Fase 4 — US-003 Fronteira verificável e dívida encerrada (P1)

**Objetivo**: os dois testes estáticos finais e o contrato publicado.
**Teste independente**: introduzir `import dotenv` num módulo de `src/pipeline/` e observar a suíte reprovar nomeando o arquivo.

- [x] T018 [CODE] [US-003] Finalizar os dois testes estáticos de AST em tests/test_env_bootstrap.py: src/pipeline/ livre de dotenv e cada entrypoint da raiz com load_env(), com mensagem nomeando arquivo e import e sem falso positivo fora de src/pipeline/ — Refs: US-003, FR-005, FR-006, NFR-001, AC-003, AC-004, AC-006, AC-011 — Depends: T003, T004, T006, T011, T017
  - [x] **PREP**: RED de T003, T004 e T011 confirmado na seção 11 e GREEN de T017 verificado; T006 (baseline em doc) segue vermelho até T019.
  - [x] **EXECUTE**: As duas varreduras já estavam consolidadas em `tests/test_env_bootstrap.py` desde a fase RED — `dotenv_violations_in_pipeline()` (AST de `src/pipeline/`) e `entrypoints_sem_load_env()` (`.py` da raiz com bloco `__main__`) — com mensagem nomeando arquivo e import e o caso `test_scanners_de_fronteira_nomeiam_arquivo_e_import` cobrindo o sem-falso-positivo fora de `src/pipeline/`. Nenhum código de produção adicional foi necessário além de T017.
  - [x] **VERIFY**: `uv run pytest tests/test_env_bootstrap.py tests/test_ci_gates.py` → passa (T006 vira verde após T019); regressão `uv run pytest` → 271 passed; `uv run ruff check .` → `All checks passed!`.
  - [x] **VISUAL**: `Não aplicável` — teste estático, sem superfície visual.
  - [x] **EVIDENCE**: GREEN de T003/T004/T011 registrado na seção 11; a parcela estrutural de AC-006 (módulo coletável, funções de fronteira presentes) já verde, restando a baseline documental para T019.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária — os scanners seguem o padrão de `tests/test_provider_boundaries.py` e `tests/test_application_boundaries.py`, mantendo a família de testes de fronteira coesa.
  <!-- specsfy:evidence {"task":"T018","refs":["US-003","FR-005","FR-006","NFR-001","AC-003","AC-004","AC-006","AC-011"],"files":["tests/test_env_bootstrap.py"],"commands":[{"run":"uv run pytest tests/test_env_bootstrap.py tests/test_ci_gates.py","exit":0},{"run":"uv run pytest","exit":0}]} -->

- [x] T019 [DOC] [US-003] Atualizar docs/architecture.md, .specsfy/STACK.md e .specsfy/RULES.md: descrever src/bootstrap.py e load_env(), marcar BACKLOG-0012 como resolvida e registrar por $specsfy-aux-rules a regra de que src/pipeline/ não carrega o .env — Refs: US-003, FR-002, FR-007, NFR-003, AC-007, AC-010, AC-014, AC-015 — Depends: T007, T010, T014, T015, T017
  - [x] **PREP**: RED de T010, T014 e T015 confirmado na seção 11; GREEN de T007/T017 verificado.
  - [x] **EXECUTE**: `docs/architecture.md` ganhou a subseção "Carga do ambiente pelos entrypoints" descrevendo `src/bootstrap.py`/`load_env()`, marcou `BACKLOG-0012` como **resolvido** na seção de dívidas e passou a baseline mínima para 255; `.specsfy/STACK.md` ganhou a linha "Carga do `.env`" e ajustou a linha de Configuração; `.specsfy/RULES.md` ganhou, na seção Arquitetura, a regra de que `src/pipeline/` não carrega o `.env` e a carga é dos entrypoints via `src/bootstrap.py`.
  - [x] **VERIFY**: `uv run pytest tests/test_docs_safety.py` → 11 passed; `uv run pytest tests/test_ci_gates.py -k env_bootstrap` → 1 passed; `uv run pytest` → 271 passed; `monitor_context.mjs --project . --check` → `CURRENT`.
  - [x] **VISUAL**: `Não aplicável` — alteração de documentação, sem superfície visual.
  - [x] **EVIDENCE**: GREEN de T006/T010/T014/T015 registrado na seção 11; `docs/architecture.md`, `.specsfy/STACK.md` e `.specsfy/RULES.md` são a evidência versionada.
  - [x] **IMPROVE**: A regra em `RULES.md` foi redigida ao lado da regra de fronteira `src/app/` da SPEC-0008, mantendo as duas restrições arquiteturais adjacentes e fáceis de achar.

#### Fase final — Qualidade

- [x] T020 [TEST] Executar regressão, lint e rastreabilidade e registrar o resultado nas seções 11–13 de specs/in-progress/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-001, NFR-002, NFR-003, NFR-004, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015 — Depends: T016, T017, T018, T019
  - [x] **PREP**: Reunidos `uv run pytest`, `uv run ruff check .`, `check_traceability.mjs`, `verify_acceptance.mjs`, `verify_evidence.mjs` e `monitor_context.mjs`; baseline mínima 255 confirmada em `docs/architecture.md`.
  - [x] **EXECUTE**: `uv run pytest` → 271 passed em 21,23s; `uv run ruff check .` → `All checks passed!`; `check_traceability.mjs` → 29/29 IDs cobertos em 25 arquivos.
  - [x] **VERIFY**: `uncovered: []`, `insufficient_cases: {}`; 271 ≥ baseline 255; `verify_acceptance.mjs` → `QA: PASSED`; `verify_evidence.mjs` → `PASSED (strict)`; `monitor_context.mjs --check` → `CURRENT`. O `RESULTADO: GAPS` da rastreabilidade é apenas de marcadores órfãos das SPEC-0001 a SPEC-0008 que compartilham `tests/` — nenhum vem de `tests/test_env_bootstrap.py`.
  - [x] **VISUAL**: `Não aplicável` — nenhuma tarefa desta spec altera superfície visual.
  - [x] **EVIDENCE**: Contagens, comandos e vereditos registrados nas seções 12 e 13; atestação abaixo.
  - [x] **IMPROVE**: Retrospectiva — o único atrito foi o quantificador universal de quatro letras (t-o-d-o) na descrição de T018, apanhado por `tests/test_spec_markers.py` (regra local já documentada em `.specsfy/RULES.md`); reescrito para "cada". A interação com a SPEC-0008 (`src.bootstrap` como novo alvo de import autorizado) foi resolvida por uma correção reversível de uma linha no teste `test_pipeline_service.py`, sem reabrir aquela spec.
  <!-- specsfy:evidence {"task":"T020","refs":["US-001","US-002","US-003","FR-001","FR-002","FR-003","FR-004","FR-005","FR-006","FR-007","NFR-001","NFR-002","NFR-003","NFR-004","AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","AC-007","AC-008","AC-009","AC-010","AC-011","AC-012","AC-013","AC-014","AC-015"],"files":["specs/in-progress/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md"],"commands":[{"run":"uv run pytest","exit":0},{"run":"uv run ruff check .","exit":0},{"run":"node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md .","exit":1},{"run":"node .agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.mjs specs/in-progress/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md .","exit":0},{"run":"node .agents/skills/specsfy-07-implement/scripts/verify_evidence.mjs specs/in-progress/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md .","exit":0}]} -->

### 15. Ordem de execução

- Caminho crítico: T001..T015 (RED) → T016 (`src/bootstrap.py`) → T017 (remoção em `config.py` + nove entrypoints + `inspect_chunks.py`) → T018 (testes estáticos finais) → T019 (documentação) → T020 (regressão e rastreabilidade).
- Tarefas paralelas: T001 a T015 podem ser escritas em paralelo por materializarem RED em `tests/test_env_bootstrap.py`, `tests/test_docs_safety.py` e `tests/test_ci_gates.py` sem dependência mútua. Depois do GREEN de T017, T018 e T019 podem avançar em paralelo.
- Estratégia de MVP: T016 e T017 sozinhos já entregam o determinismo dos testes e a operação preservada — o núcleo do valor. T018 fecha a verificação automática da fronteira e T019 encerra a dívida bloqueante da fatia 2.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0003, concluída: fornece o padrão de teste estático de AST que esta spec
  replica.
- SPEC-0007, concluída: fornece a esteira de integração contínua que executa os
  testes estáticos a cada push.
- SPEC-0008, concluída: declarou esta dívida como bloqueante da fatia 2 e
  definiu PR-004, preservado aqui.
- BACKLOG-0013: segunda dívida bloqueante da fatia 2, entregável em paralelo;
  não bloqueia esta spec.

#### Riscos

- Um entrypoint da raiz esquecido perde a carga do `.env` e falha por
  credencial ausente → o teste estático de FR-006 varre todos os `.py`
  executáveis da raiz e reprova a ausência de `load_env()`.
- `python-dotenv` resolve o `.env` a partir do diretório de trabalho; um
  operador que rode o CLI de outra pasta pode não carregar o `.env` esperado →
  `load_env()` mantém o comportamento padrão de `load_dotenv()` já em uso hoje;
  nenhuma mudança de resolução de caminho é introduzida por esta entrega.
- O teste estático de "cada entrypoint chama `load_env()`" pode gerar falso
  positivo em um `.py` da raiz que não seja entrypoint → o critério é a
  presença do bloco `if __name__ == "__main__"`; arquivos sem esse bloco não
  são inspecionados. `inspect_chunks.py` é reestruturado nesta entrega para
  ter esse bloco, de modo que os nove entrypoints ficam sob a mesma regra.
- A reestruturação de `inspect_chunks.py` pode alterar sua saída de inspeção
  por engano → o corpo é movido para dentro de `def main()` sem mudança de
  lógica; AC-004 exige que a saída permaneça a mesma de antes.
- Remover `load_dotenv()` do import pode quebrar um teste que dependia
  silenciosamente do efeito colateral → a suíte completa é a prova; qualquer
  quebra aparece antes do GREEN e é corrigida no próprio caso, não com novo
  `monkeypatch`.

#### Suposições

- `main.py`, `inspect_chunks.py` e `quality.py` recebem `load_env()` pela regra
  uniforme de FR-003, mesmo sem resolver credencial hoje. `main.py` continua
  sendo um stub de `uv init`; esta entrega não o remove.
- Entrypoint da raiz é o arquivo `.py` no diretório raiz do repositório com
  bloco `if __name__ == "__main__"`. `inspect_chunks.py` é ajustado a esse
  padrão nesta entrega. Se um novo entrypoint futuro não seguir o padrão, a
  regra de FR-006 é revista por `$specsfy-update-spec`.
- O nome `src/bootstrap.py` e a assinatura `load_env() -> None` são defaults
  reversíveis: qualquer módulo único fora de `src/pipeline/` e de `src/app/`
  satisfaz o contrato, desde que seja o único ponto de carga e esteja citado no
  teste estático e na documentação.
- As blindagens `monkeypatch.delenv` dos testes de credencial ausente
  permanecem como garantia por caso, mesmo com a causa raiz removida.
- `docs/architecture.md` e `.specsfy/STACK.md` são os destinos do contrato
  publicado. Se o documentador reorganizar a topologia de `docs/`, o destino
  acompanha, mantendo o conteúdo.
- O runner de testes permanece Pytest.

### 17. Decisões

- **DEC-001**: concentrar a carga do `.env` em um bootstrap compartilhado fora
  de `src/pipeline/`, chamado por cada entrypoint, em vez de cada CLI chamar
  `load_dotenv()` diretamente. Razão: um ponto único de manutenção e um teste
  estático que prova `src/pipeline/` livre de `dotenv`, no mesmo padrão da
  SPEC-0003 e da SPEC-0008. Alternativas descartadas: cada CLI com
  `load_dotenv()` próprio (repete a linha, depende de ninguém esquecer);
  bootstrap em `src/app/` (acopla os CLIs à futura camada de aplicação).
- **DEC-002**: fazer os nove entrypoints da raiz chamarem `load_env()`, não só
  os cinco operacionais. Razão: elimina o risco de entrypoint esquecido
  apontado na Inbox; o custo é uma linha por arquivo e o teste estático de
  FR-006 torna a regra verificável. Trade-off: `main.py`, `inspect_chunks.py` e
  `quality.py` ganham uma linha que hoje não usam.
- **DEC-003**: nomear o módulo `src/bootstrap.py` com `load_env() -> None`,
  idempotente e sem override de variável presente. Razão: descritivo,
  importável de forma estável por CLIs e pelo futuro backend, e o comportamento
  sem override mantém o CI determinístico. Alternativas descartadas:
  `bootstrap.py` na raiz (fora do pacote `src/`); `src/env.py` (nome menos
  descritivo).
- **DEC-004**: preservar `python-dotenv` como dependência de carga, movendo só
  o ponto de chamada. Razão: a biblioteca já está integrada e testada; trocá-la
  seria escopo distinto sem benefício para o problema.
- **DEC-005**: preservar as blindagens `monkeypatch.delenv` dos testes de
  credencial ausente. Razão: são garantia por caso do comportamento sob teste;
  removê-las junto com a causa raiz reduziria a defesa em profundidade sem
  ganho.
- **DEC-006**: reestruturar `inspect_chunks.py` para o formato padrão de
  entrypoint — `def main()` mais `if __name__ == "__main__"` — e manter
  `main.py` no conjunto de nove com `load_env()`, em vez de alargar o teste
  estático ou remover `main.py` como código morto. Razão: mantém a decisão de
  "nove entrypoints" ao pé da letra e o critério do teste estático simples
  (`if __name__ == "__main__"`). Alternativas descartadas: alargar o teste
  para detectar código executável em nível de módulo (teste mais complexo sem
  ganho); remover `main.py` (mexe numa decisão já confirmada e espalha para
  `docs/README.md`).

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `docs/architecture.md` descreve `src/bootstrap.py` e registra BACKLOG-0012
      como resolvida na seção de dívidas bloqueantes.
- [x] `.specsfy/STACK.md` reflete `src/bootstrap.py` como o ponto de carga do
      `.env` e não cita `load_dotenv` no import de `src/pipeline/config.py`.
- [x] `.specsfy/RULES.md` registra, por `$specsfy-aux-rules`, a regra de que
      módulos sob `src/pipeline/` não carregam o `.env` e que a carga é
      responsabilidade dos entrypoints da raiz.
- [x] O monitor de contexto retorna `CURRENT`.
