# Backlog: Definir a fronteira interna entre o pipeline e o backend de aplicação

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0011 |
| Status | Ready for specification |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Prontidão de integração |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M01 |
| Criado em | 2026-09-03 |
| Refinado em | 2026-09-03 |
| Spec promovida | Nenhuma |

## Ideia original

Consolidar um contrato de handoff para incorporar este componente ao rag-pipeline, separado dos gates de qualidade pela decisão de 2026-09-03.

**Reformulação confirmada em 2026-09-03 (Pergunta 1 do refinamento):** a ideia
original nasceu quando `rag-ingestion-pipeline` e `rag-pipeline` eram dois
repositórios distintos. Os commits `e2d8b1b` e `0fe7b1b` consolidaram ambos em
um único repositório, hoje chamado `rag-pipeline`. O item deixa de ser um
contrato de handoff entre repositórios e passa a ser o contrato da fronteira
interna entre o pipeline existente e o futuro backend de aplicação, dentro do
mesmo repositório. A formulação original fica preservada acima como
proveniência.

## Problema percebido

O pipeline será consumido por um backend de aplicação (FastAPI, tarefas
assíncronas e persistência) no mesmo repositório, mas não existe fronteira
declarada entre as duas camadas. Hoje qualquer código novo pode importar
`chunker`, `indexing`, `providers` ou `config` diretamente, sem contrato,
repetindo o acoplamento que a SPEC-0003 eliminou dentro dos providers. Também
não há declaração de qual é a interface Python estável, o que ela exige de
configuração, quais limites respeita e quais dívidas conhecidas o backend
herdaria.

## Pessoa afetada ou beneficiada

Marcio e quem implementar o backend de aplicação sobre o pipeline. O contrato
evita que a camada de aplicação nasça acoplada a detalhes internos que a
SPEC-0003 já isolou.

## Resultado ou valor esperado

O backend de aplicação é escrito contra uma fachada estável e explícita, com
configuração injetada, fronteira física de diretórios e dívidas conhecidas
resolvidas antes da incorporação — sem precisar ler o interior do pipeline
para descobrir o que pode consumir.

## Contexto

Fatia (b) do desmembramento do BACKLOG-0007, decidido em 2026-09-03. A fatia
(a), com Ruff e integração contínua, foi concluída na SPEC-0007.

Este item é o passo 3 e 4 da sequência registrada em
`CONTEXTO_CONTINUACAO_PROJETO_MAE.md`: definir a fronteira entre o pipeline
existente e o backend de aplicação, antes de transformar a fatia de
incorporação do BACKLOG-0008 em spec executável e antes de qualquer frontend.

A raiz do projeto-mãe está confirmada: é este repositório. `PROJECT.md` e
`.specsfy/USER-PROFILE.md` já registram a consolidação das duas fases.

## Referências relacionadas

- `specs/backlog/0007-gates-entrega-handoff.md`: item de origem. Este backlog é a fatia (b) do desmembramento decidido em 2026-09-03; o 0007 ficou com Ruff e integração contínua, concluídos na SPEC-0007. Tipo: backlog relacionado.
- `specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md`: épico cuja fatia 2 (incorporação ao backend) depende deste contrato. Atualizado em 2026-09-03 para a realidade de repositório único. Tipo: backlog relacionado.
- `CONTEXTO_CONTINUACAO_PROJETO_MAE.md`: handoff que registra o estado consolidado e a sequência recomendada de estruturação. Tipo: documentação relacionada.
- `specs/completed/0003-modularizar-providers-factory-adapter/spec.md`: precedente direto. Estabeleceu contratos neutros, factory e um teste estático de AST que impede import de SDK fora de `src/providers/`. Este item aplica o mesmo padrão à fronteira pipeline/aplicação. Tipo: spec relacionada.
- `docs/application.md` e `docs/architecture.md`: inventário das superfícies atuais e das fronteiras já documentadas. Tipo: documentação relacionada.
- `.specsfy/STACK.md` e `PROJECT.md`: capacidades, limites e tecnologias que o contrato precisa declarar. Tipo: documentação relacionada.
- `specs/backlog/0012-isolar-a-carga-do-env-nos-entrypoints.md`: dívida bloqueante confirmada na Pergunta 5, promovida da Inbox em 2026-09-03. Tipo: backlog relacionado.
- `specs/backlog/0013-cobrir-o-comportamento-dos-backends-reais-de-vector-store.md`: dívida bloqueante confirmada na Pergunta 5, promovida da Inbox em 2026-09-03. Tipo: backlog relacionado.

## Comportamento esperado

1. O código atual de `src/` passa a viver em `src/pipeline/`, preservando os módulos existentes (loader, chunker, identity, manifest, quality, validation, safety, indexing, providers, exporter, status_gate, config).
2. Um novo pacote `src/app/` recebe API, tarefas assíncronas e persistência do backend de aplicação. Ele nasce vazio ou mínimo neste item; sua implementação pertence à fatia 2 do BACKLOG-0008.
3. `src/pipeline/` expõe uma fachada de casos de uso — um módulo único, alvo estável de import — com as operações de alto nível do pipeline: executar o pipeline sobre uma base, sincronizar com o banco vetorial, validar a recuperação e consultar a base indexada.
4. A fachada recebe a configuração já resolvida como parâmetro. Nenhuma função da fachada lê `config.yaml` do disco nem depende de estado global de ambiente.
5. Ler `config.yaml`, resolver caminhos e montar o objeto de configuração continua sendo responsabilidade dos entrypoints de linha de comando na raiz.
6. Os CLIs atuais (`pipeline.py`, `search.py`, `chat.py`, `validate.py`, `upsert_from_chunks.py`) continuam na raiz e continuam funcionando com os mesmos comandos; passam a importar de `src/pipeline/` e, quando aplicável, a chamar a fachada.
7. `src/app/` consome exclusivamente a fachada. Ele não importa `chunker`, `indexing`, `providers`, `config` ou qualquer módulo interno de `src/pipeline/`.
8. As duas dívidas conhecidas estão resolvidas antes de `src/app/` receber implementação.
9. O contrato fica registrado em documentação legível, declarando fachada, entrypoints, configuração exigida, limites e dívidas.

## Regras de negócio

- `src/app/` conhece apenas a fachada de `src/pipeline/`; importar módulo interno do pipeline é violação de fronteira.
- A fachada não lê arquivo de configuração, não lê variável de ambiente e não mantém estado global: toda configuração entra por parâmetro.
- Os comandos de operação existentes não mudam de nome nem de forma de uso por causa desta reorganização.
- A reorganização de diretórios preserva o histórico do Git; nenhum módulo é reescrito do zero nesta fatia.
- Uma dívida declarada como bloqueante não pode ser contornada por decisão local durante a implementação do backend.
- O contrato descreve o que existe e o que está garantido; ele não promete comportamento ainda não implementado.

## Critérios de aceitação

```gherkin
Scenario: Reorganizar o pipeline sem quebrar a operação atual
  Given o código do pipeline vive hoje em src/ e é operado pelos CLIs da raiz
  When src/ passa a ser src/pipeline/ e os CLIs passam a importar do novo caminho
  Then a suíte completa continua verde
  And cada CLI da raiz continua sendo executado com o mesmo comando de antes

Scenario: Consumir o pipeline apenas pela fachada
  Given um pacote src/app/ destinado ao backend de aplicação
  When algum módulo de src/app/ importa um módulo interno de src/pipeline/
  Then um teste estático de fronteira falha e identifica o import proibido
  And a violação é apontada antes do merge pela esteira de integração contínua

Scenario: Executar o pipeline com configuração injetada
  Given uma configuração já resolvida em memória, sem config.yaml no disco
  When a fachada é chamada para executar o pipeline sobre uma base
  Then a execução acontece usando somente a configuração recebida por parâmetro
  And nenhuma leitura de config.yaml ou de variável de ambiente é necessária

Scenario: Impedir a incorporação com dívida bloqueante aberta
  Given uma das duas dívidas declaradas como bloqueantes ainda não foi resolvida
  When alguém propõe iniciar a implementação de src/app/
  Then o contrato registra a dívida como impedimento explícito
  And a fatia de incorporação do BACKLOG-0008 permanece bloqueada

Scenario: Declarar o contrato para quem vai implementar o backend
  Given a fronteira e a fachada definidas
  When alguém precisa escrever código em src/app/
  Then encontra em documentação a fachada, os entrypoints, a configuração exigida, os limites e as dívidas conhecidas
  And não precisa ler o interior de src/pipeline/ para descobrir o que pode consumir
```

## Qualidades e operação

- Segurança: a fachada não recebe nem devolve segredo; credencial continua resolvida fora dela, como hoje. O contrato declara isso explicitamente para que o backend não passe a transportar chave por parâmetro de caso de uso.
- Privacidade: nenhum dado novo é coletado nesta fatia; a fronteira não altera o que é gravado em manifesto, chunks ou banco vetorial.
- Desempenho e volume: a fachada é síncrona nesta fatia. A execução assíncrona pertence a `src/app/` e será definida na fatia 2 do BACKLOG-0008; o contrato precisa declarar que chamar a fachada bloqueia a thread chamadora.
- Auditoria e observabilidade: as contagens de previstos, inseridos, mantidos e removidos já produzidas pelo pipeline precisam ser alcançáveis pelo retorno da fachada, não apenas impressas em log, para que o backend possa persistir e exibir esses números.

## Dependências

- BACKLOG-0012, **bloqueante**: enquanto `load_dotenv()` rodar no import de `config.py`, a regra de configuração injetada é contornável e a suíte continua dependendo do `.env` da máquina.
- BACKLOG-0013, **bloqueante**: `_QdrantBackend`, `_ChromaBackend` e `_PineconeBackend` nunca são executados por teste; incorporar o pipeline a um backend assíncrono antes disso move erro de tradução de SDK para dentro de execuções de produção.
- SPEC-0003, concluída: fornece o padrão de contrato neutro, factory e teste estático de AST que este item replica na fronteira pipeline/aplicação.
- BACKLOG-0008, fatia 2: consome este contrato; não pode virar spec executável antes dele.

## Situações de erro

- Import proibido de `src/app/` para dentro de `src/pipeline/`: o teste estático de fronteira falha, nomeia o arquivo e o módulo importado e bloqueia o merge.
- Chamada da fachada sem configuração válida: falha imediata e explícita antes de qualquer acesso remoto, mantendo a política fail-closed já existente em `src/safety.py`.
- Reorganização de diretórios que quebre um CLI da raiz: a suíte falha; a fatia não é considerada entregue enquanto os cinco comandos não funcionarem como antes.
- Tentativa de iniciar `src/app/` com dívida bloqueante aberta: o contrato registra o impedimento; a decisão de prosseguir mesmo assim exige reabrir este item, não uma escolha local.

## Escopo

- Dentro: mover `src/` para `src/pipeline/`; criar `src/app/` como destino declarado do backend; criar a fachada de casos de uso; injetar configuração por parâmetro; manter os CLIs da raiz funcionando; criar o teste estático de fronteira; declarar o contrato em documentação; registrar as duas dívidas bloqueantes.
- Fora: implementar FastAPI, rotas HTTP, tarefas assíncronas, persistência própria, autenticação, tenant/projeto/roles e qualquer tela — tudo isso pertence às fatias 2 e 3 do BACKLOG-0008. Também fora: reescrever a lógica interna do pipeline, mudar o contrato de `config.yaml` para o operador e resolver as duas dívidas bloqueantes dentro deste item (elas precisam de itens próprios).

## Dúvidas, decisões e riscos

- Decisão confirmada em 2026-09-03: o BACKLOG-0007 foi desmembrado em duas fatias porque Ruff e integração contínua são infraestrutura de qualidade mensurável, enquanto o contrato de fronteira depende de decisões de arquitetura. Mantê-los juntos atrasaria a primeira.
- Contradição resolvida na Pergunta 1: a premissa de dois repositórios, presente na formulação original e no BACKLOG-0008, foi superada pela consolidação commitada em `e2d8b1b` e `0fe7b1b`. O item passa a tratar de fronteira interna, não de handoff entre repositórios. A raiz do projeto-mãe é este repositório.
- Decisão confirmada na Pergunta 2: o contrato inclui a decisão de estrutura de diretórios, porque ela delimita fisicamente o que é pipeline e o que é aplicação.
- Decisão confirmada na Pergunta 3: o layout é `src/pipeline/` para o código atual e `src/app/` para API, tarefas e persistência, mantendo um único pacote Python e uma única configuração de projeto.
- Decisão confirmada na Pergunta 4: os CLIs continuam na raiz como entrypoints finos, importando de `src/pipeline/`; nenhum comando de operação muda.
- Decisão confirmada na Pergunta 5: as duas dívidas conhecidas bloqueiam a incorporação. Um backend assíncrono chamando o pipeline agravaria tanto o acoplamento do `.env` quanto a ausência de prova dos backends reais.
- Decisão confirmada na Pergunta 6: a fronteira é uma fachada nova de casos de uso; `src/app/` nunca conhece chunker, indexing ou providers diretamente.
- Decisão confirmada na Pergunta 7: a configuração entra na fachada por parâmetro; ler `config.yaml` fica restrito aos CLIs da raiz.
- Risco registrado: mover `src/` para `src/pipeline/` toca todos os imports do repositório e os 238 testes. A fatia precisa ser executada de uma vez, com a suíte como prova, e não incrementalmente por módulo.
- Risco registrado: a fachada pode virar um repasse fino sem valor se apenas reexportar funções internas. O teste de fronteira previne o sintoma, mas não a causa; a spec precisa declarar as operações de alto nível pelo caso de uso, não pelo módulo de origem.
- Resolvido em 2026-09-03: as duas dívidas bloqueantes foram promovidas da Inbox e passaram a ser o BACKLOG-0012 e o BACKLOG-0013, com rastreio próprio.
- Nenhuma lacuna aplicável permanece neste item.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Brief pronto para especificar

1. **Problema e objetivo:** não existe fronteira declarada entre o pipeline e o futuro backend de aplicação no mesmo repositório; o objetivo é criar essa fronteira antes que a camada de aplicação nasça acoplada.
2. **Atores:** Marcio e quem implementar o backend de aplicação.
3. **Escopo:** `src/pipeline/`, `src/app/`, fachada de casos de uso, configuração injetada, CLIs preservados, teste estático de fronteira e contrato documentado.
4. **Fora de escopo:** FastAPI, tarefas assíncronas, persistência, autenticação, telas e a resolução das duas dívidas bloqueantes (itens próprios).
5. **Jornadas e regras essenciais:** `src/app/` consome apenas a fachada; a fachada recebe configuração por parâmetro; os comandos do operador não mudam; dívida bloqueante impede a incorporação.
6. **Aceite:** cinco cenários Given/When/Then cobrindo reorganização sem quebra, fronteira verificada por teste estático, execução com configuração injetada, bloqueio por dívida aberta e contrato legível.
7. **Restrições:** histórico preservado, suíte verde como prova, política fail-closed mantida, nenhum segredo transportado pela fachada.
8. **Suposições confirmadas:** a raiz do projeto-mãe é este repositório; o padrão de fronteira replica o já provado pela SPEC-0003.
9. **Decisões abertas:** nenhuma. As duas dívidas bloqueantes viraram BACKLOG-0012 e BACKLOG-0013.

## Próximo passo

Criar a spec desta fatia com `$specsfy-03-specify`. O BACKLOG-0012 e o
BACKLOG-0013 são bloqueantes da implementação de `src/app/`, não da
especificação desta fronteira: eles podem ser especificados e entregues em
paralelo.
