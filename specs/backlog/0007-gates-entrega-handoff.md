# Backlog: Instalar o Ruff e criar a esteira de integração contínua

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0007 |
| Status | Promoted |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Prontidão de entrega |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M01 |
| Criado em | 2026-08-31 |
| Refinado em | 2026-09-03 |
| Spec promovida | `specs/draft/0007-ruff-e-esteira-de-integracao-continua/spec.md` |

## Ideia original

Consolidar Ruff, testes críticos, documentação segura e um contrato de handoff para incorporar este componente ao rag-pipeline.

## Problema percebido

Texto original da captura, preservado: "A suíte atual tem nove testes, Ruff não
está disponível no ambiente e a documentação ainda contém comandos destrutivos,
impedindo considerar o componente pronto para integração."

### Estado verificado em 2026-09-03

O diagnóstico acima envelheceu. Dois dos três problemas descritos já não existem:

| Afirmação da captura | Estado real |
| --- | --- |
| "A suíte atual tem nove testes" | 221 casos em 20 arquivos de teste |
| "a documentação ainda contém comandos destrutivos" | Resolvido pela SPEC-0001, com guarda de regressão em `tests/test_docs_safety.py` varrendo quatro documentos publicados |
| "Ruff não está disponível no ambiente" | Continua verdade |

As dependências também mudaram: os seis backlogs que este item aguardava foram
entregues como SPEC-0001 a SPEC-0006, todas `Complete`.

O que sobra é específico e mensurável:

1. O `pyproject.toml` declara `[tool.ruff]` com `extend-exclude = [".agents"]`,
   mas o Ruff **não está nas dependências**. Existe configuração sem ferramenta.
2. `.github/workflows/` não existe. Nenhuma verificação roda sozinha.
3. A SPEC-0006 fechou com um item da Definition of Done aberto justamente por
   isso: `uv run ruff check` não executa. Este item é o dono dessa pendência.

## Pessoa afetada ou beneficiada

Mantenedores do componente, que hoje dependem de disciplina manual para lembrar
de rodar as verificações antes de publicar.

## Resultado ou valor esperado

Toda publicação passa por Ruff e Pytest sem depender de alguém lembrar, e uma
reprovação impede o merge. O item da Definition of Done que a SPEC-0006 deixou
aberto fecha.

## Contexto

Item P1 do milestone M01. Em 2026-09-03 o item foi desmembrado em duas fatias:
esta, com Ruff e integração contínua, e o BACKLOG-0011, com o contrato de
handoff para o projeto-mãe. O motivo do corte está registrado em decisões.

### Medição do Ruff sobre o código atual

Executada com `uvx ruff check`, de forma efêmera, sem alterar `pyproject.toml`
nem `uv.lock`. Ruff 0.16.5.

| Configuração | Achados | Alcança os defeitos semânticos do código novo | Alcança largura de linha |
| --- | --- | --- | --- |
| Padrão do Ruff, nada declarado | 3 | Sim | Não |
| `select = E,F,I,UP,B,SIM`, largura 88 | 124 | Não | Sim |
| `select = E,F,I,UP,B,SIM`, largura 100 | 18 | Não | Sim |
| `extend-select = E501,I,UP,B,SIM`, largura 100 | 19 | Sim | Sim |
| `extend-select = E501,I,UP,B,SIM`, largura 110 | 8 | Sim | Sim |

Mecânica que a medição expôs e que a especificação precisa preservar: no Ruff,
`select` **substitui** o conjunto padrão e `extend-select` **soma** a ele. O
padrão do Ruff 0.16 cobre `E4`, `E7`, `E9` e `F`, mas não `E5`, onde vive o
`E501`. Por isso `select = E,F,...` e o padrão são conjuntos parcialmente
disjuntos: o primeiro pega largura de linha e perde `TRY004`, `PIE810` e
`ISC004`; o segundo faz o inverso.

Não existe dívida acumulada de lint neste repositório. Dos 19 achados da
configuração escolhida, 16 são `E501` em código pré-existente — 11 deles em
`tests/test_client_neutrality.py`, que mantém listas longas de identificadores —
e 3 são defeitos semânticos introduzidos pela própria SPEC-0006, em
`quality.py:70`, `src/quality.py:292` e `src/quality.py:608`.

## Referências relacionadas

- `.specsfy/RULES.md`, seção Testes: regra confirmada em 2026-08-31 que exige Ruff e Pytest verdes localmente e em integração contínua a cada push de branch de fase. Tipo: documentação normativa do projeto.
- `pyproject.toml`: declara `[tool.ruff]` sem que o Ruff seja dependência. Tipo: configuração afetada.
- `specs/completed/0006-gate-qualidade-chunks-metadados/spec.md`, seção 13: registra a pendência externa aceita, cujo dono é este item. Tipo: spec relacionada.
- `docs/testing.md`: registra o Ruff como gate confirmado ainda não instalado e atribui a lacuna a este item. Tipo: documentação relacionada.
- `tests/test_docs_safety.py`: guarda de regressão que já resolve a parte documental da captura original. Tipo: código relacionado.
- `specs/backlog/0011-contrato-handoff-projeto-mae.md`: fatia (b) desmembrada deste item em 2026-09-03. Tipo: backlog relacionado.
- Linear `LEAD-92`: tracking do item no milestone.

## Comportamento esperado

1. O mantenedor executa `uv run ruff check` localmente e a verificação roda,
   porque o Ruff passou a ser dependência de desenvolvimento do projeto.
2. Os 19 achados da configuração escolhida são corrigidos, e a verificação
   local fica verde.
3. O mantenedor publica um push em uma branch de fase.
4. O GitHub Actions executa Ruff e a suíte Pytest sobre esse push, sem
   intervenção manual.
5. O resultado aparece no commit e no pull request.
6. Enquanto a verificação estiver reprovada, o merge do pull request fica
   bloqueado.
7. Com a esteira verde, o item da Definition of Done da SPEC-0006 pode ser
   marcado como cumprido.

## Regras de negócio

- O Ruff entra como dependência do grupo de desenvolvimento, junto do Pytest;
  não é dependência de execução do pipeline.
- A configuração usa `extend-select = ["E501", "I", "UP", "B", "SIM"]` e
  `line-length = 100`, preservando o conjunto padrão do Ruff em vez de
  substituí-lo.
- A esteira executa exatamente as mesmas verificações disponíveis localmente:
  `uv run ruff check` e `uv run pytest`. Um comando que só existe na esteira
  não é reproduzível pelo mantenedor.
- A reprovação bloqueia o merge. Um resultado que pode ser ignorado não cumpre
  a regra confirmada em `.specsfy/RULES.md`.
- A esteira não recebe credencial, token nem variável de ambiente do projeto:
  nenhuma suíte exige rede, conforme `docs/testing.md`.
- O registro de execução não expõe segredo algum.

## Critérios de aceitação

```gherkin
Scenario: Executar o Ruff localmente
  Given o Ruff declarado como dependência de desenvolvimento
  When o mantenedor executa `uv run ruff check`
  Then a verificação roda e não acusa nenhum achado
  And a configuração aplicada preserva o conjunto padrão do Ruff

Scenario: Preservar os defeitos que só o conjunto padrão alcança
  Given a configuração declarada no pyproject.toml
  When a verificação percorre o código do repositório
  Then regras do conjunto padrão como TRY004, PIE810 e ISC004 continuam ativas
  And as famílias acrescentadas por extend-select também são aplicadas

Scenario: Verificar automaticamente um push em branch de fase
  Given a esteira de integração contínua configurada
  When o mantenedor publica um push em uma branch de fase
  Then o Ruff e a suíte Pytest são executados sem intervenção manual
  And o resultado fica visível no commit

Scenario: Bloquear o merge diante de reprovação
  Given um pull request cuja verificação automática reprovou
  When alguém tenta concluir o merge
  Then o merge é impedido enquanto a verificação não passar

Scenario: Executar sem segredo
  Given a esteira de integração contínua
  When ela executa a suíte completa
  Then nenhuma credencial, token ou variável de ambiente do projeto é necessária
  And o registro de execução não expõe valor sensível

Scenario: Fechar a pendência da SPEC-0006
  Given a esteira verde e o Ruff disponível localmente
  When o mantenedor revisa a Definition of Done da SPEC-0006
  Then o item que exige `uv run ruff check` pode ser marcado como cumprido
```

## Qualidades e operação

- **Segurança:** a esteira não recebe segredo. O `.env` e o `config.yaml` estão
  fora do índice do Git e não são necessários para a suíte.
- **Privacidade:** nenhum dado de base real trafega; os testes usam conjuntos
  sintéticos e dublês.
- **Desempenho e volume:** referência local de `uv run pytest` é de 10 a 13
  segundos para 221 casos; o Ruff é praticamente instantâneo. A esteira não
  precisa de paralelismo nem de matriz de versões.
- **Auditoria e observabilidade:** o resultado de cada execução fica no
  histórico do repositório, associado ao commit, e é a evidência reproduzível
  de qualidade exigida para encerrar o marco.

## Dependências

- Nenhuma pendente. As seis fatias que este item aguardava foram entregues como
  SPEC-0001 a SPEC-0006, todas `Complete`.
- A configuração de bloqueio de merge é ajuste no repositório do GitHub, fora do
  código, e depende de acesso administrativo de quem o mantém.

## Situações de erro

- Ruff acusa achado novo em um push → a esteira reprova e o merge fica
  bloqueado até a correção.
- Suíte reprova por caso instável → o caso deve ser corrigido ou isolado; não
  se desliga a verificação para destravar o merge.
- Esteira indisponível por falha da plataforma → o mantenedor pode reexecutar;
  a verificação local permanece disponível como caminho reproduzível.
- Ruff muda de versão e passa a acusar regra nova → a versão é fixada nas
  dependências, e a atualização é decisão explícita, não efeito colateral.

## Escopo

- **Dentro:** Ruff como dependência de desenvolvimento com versão fixada;
  configuração `extend-select` e `line-length` no `pyproject.toml`; correção dos
  19 achados; workflow do GitHub Actions executando `uv run ruff check` e
  `uv run pytest` a cada push de branch de fase e em pull request; configuração
  do check como obrigatório para merge; atualização de `docs/testing.md` e do
  registro do gate; fechamento do item pendente da Definition of Done da
  SPEC-0006.
- **Fora:** contrato de handoff para o projeto-mãe, que passou ao BACKLOG-0011;
  pipeline de deploy, publicação de pacote e ambientes gerenciados; APM,
  tracing distribuído e métricas em serviço externo; formatação automática por
  `ruff format`, que não foi decidida; matriz de versões de Python; qualquer
  funcionalidade do MVP do projeto-mãe.

## Dúvidas, decisões e riscos

- **Decisão de 2026-08-31, durante `$specsfy-setup`:** o critério de "pronto" do
  marco exige Ruff e Pytest verdes localmente e em integração contínua a cada
  push de branch de fase. Registrada em `.specsfy/RULES.md`, seção Testes.
- **Decisão da Pergunta 1, 2026-09-03:** desmembrar o item em duas fatias. Ruff
  e integração contínua são infraestrutura de qualidade mensurável; o contrato
  de handoff é um documento de interface entre repositórios que depende de
  decisões do projeto-mãe. Juntos, o segundo atrasaria o primeiro. A fatia (b)
  virou o BACKLOG-0011.
- **Decisão da Pergunta 2:** medir antes de escolher, executando o Ruff de forma
  efêmera com `uvx`, sem instalar nada no projeto. A medição está registrada em
  `Contexto`.
- **Decisão da Pergunta 3:** adotar `extend-select = ["E501", "I", "UP", "B",
  "SIM"]` com `line-length = 100`, corrigindo os 19 achados. A primeira
  formulação desta pergunta recomendava `select = ["E", "F", "I", "UP", "B",
  "SIM"]`, sob a premissa errada de que seria um superconjunto do padrão; a
  medição mostrou que `select` substitui o padrão e deixaria de fora os três
  defeitos semânticos do código recém-entregue. A recomendação foi corrigida
  antes da escolha.
- **Decisão da Pergunta 4:** a reprovação bloqueia o merge, e a verificação roda
  tanto em push de branch de fase quanto em pull request.
- **Suposição sustentada por evidência, não confirmada verbalmente:** a
  plataforma é o GitHub Actions. O remoto do repositório é
  `github.com/marciohernandez/rag-ingestion-pipeline`. Se a intenção for outra
  plataforma, a especificação precisa saber antes de começar.
- **Suposição:** a esteira usa Python 3.12 e `uv`, coerentes com
  `.python-version`, `requires-python = ">=3.12"` e o comando `uv run` já usado
  em toda a documentação. Uma única versão, sem matriz.
- **Risco:** a configuração de bloqueio de merge é ajuste no site do GitHub, não
  arquivo do repositório. Ela não é versionada, não aparece em revisão de código
  e depende de acesso administrativo; a especificação deve tratá-la como passo
  explícito e verificável, não como efeito do workflow.
- **Risco:** fixar a versão do Ruff evita que uma atualização introduza regra
  nova e reprove um push sem mudança de código. Em compensação, a atualização
  passa a exigir ação deliberada.
- **Observação registrada:** os três defeitos semânticos que a configuração
  escolhida acusa foram introduzidos pela SPEC-0006, concluída horas antes deste
  refinamento. O código pré-existente não tem nenhum achado semântico. Isso
  reforça o valor da esteira: sem ela, defeitos entram no repositório sem
  qualquer sinal.
- **Nenhuma lacuna aplicável permanece.**

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Brief pronto para especificar

1. **Problema e objetivo:** o repositório tem configuração de Ruff sem a
   ferramenta e nenhuma verificação automática. O objetivo é tornar Ruff e
   Pytest executáveis localmente e obrigatórios a cada publicação.
2. **Atores:** o mantenedor do componente, hoje único responsável por lembrar de
   rodar as verificações.
3. **Escopo:** Ruff como dependência com versão fixada e configuração
   `extend-select`; correção dos 19 achados; workflow do GitHub Actions; check
   obrigatório para merge; atualização da documentação de testes; fechamento do
   item pendente da SPEC-0006.
4. **Fora de escopo:** contrato de handoff, deploy, publicação, observabilidade
   externa, `ruff format` e matriz de versões.
5. **Jornada essencial:** rodar a verificação local verde, publicar um push, ver
   a esteira executar sozinha e encontrar o merge bloqueado quando ela reprovar.
6. **Aceite:** os seis cenários Given/When/Then desta entrada cobrem execução
   local, preservação do conjunto padrão, execução automática, bloqueio de
   merge, ausência de segredo e fechamento da pendência da SPEC-0006.
7. **Restrições:** as mesmas verificações localmente e na esteira; nenhum
   segredo; versão do Ruff fixada; `extend-select` em vez de `select`.
8. **Suposições confirmadas:** GitHub Actions como plataforma, sustentada pelo
   remoto do repositório; Python 3.12 com `uv`, versão única.
9. **Decisões abertas:** nenhuma. Um ponto exige atenção da especificação: o
   bloqueio de merge é configuração fora do repositório e precisa de passo
   próprio e verificável.

## Próximo passo

Promovido em 2026-09-03 para
`specs/draft/0007-ruff-e-esteira-de-integracao-continua/spec.md`. Este item
preserva a proveniência e a medição do Ruff, mas deixa de governar o
comportamento: a fonte normativa é a spec.
