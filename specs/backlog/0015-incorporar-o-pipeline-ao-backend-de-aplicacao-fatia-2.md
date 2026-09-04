# Backlog: Incorporar o pipeline ao backend de aplicação (fatia 2)

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0015 |
| Status | Promoted |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Backend de aplicação sobre a fachada do pipeline |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M01 |
| Criado em | 2026-09-04 |
| Refinado em | 2026-09-04 |
| Spec promovida | `specs/draft/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md` (SPEC-0012) |

## Ideia original

Incorporar o pipeline ao backend de aplicação: criar o contrato FastAPI, a tarefa assíncrona e a persistência sobre a fachada src/pipeline/service.py, para que o frontend da fatia 3 tenha o que consumir.

## Problema percebido

O pipeline hoje só é operável por CLI síncrona. Não existe API HTTP, execução assíncrona nem persistência de execuções, contagens, erros e consultas; sem isso, nenhum frontend pode acompanhar ou disparar o pipeline.

## Pessoa afetada ou beneficiada

Marcio, como owner que vai demonstrar a fatia funcional à equipe de consultoria, e quem consumir esta API a partir do frontend da fatia 3.

## Resultado ou valor esperado

Um backend FastAPI capaz de receber uma base Markdown (upload ou base preparada), agendar o processamento sem bloquear a requisição, expor estado/contagens/erros por execução, permitir consulta na base indexada e aplicar tenant/projeto/permissões desde esta fatia.

## Contexto

Fatia 2 do épico BACKLOG-0008 (Finalizar pipeline de documentos e criar front demonstrável). Pré-requisito BACKLOG-0011 concluído (SPEC-0008: fronteira interna e fachada síncrona em src/pipeline/service.py). Dívidas bloqueantes BACKLOG-0012 (SPEC-0009) e BACKLOG-0013 (SPEC-0011) concluídas. Fatia 3 (frontend) depende desta fatia.

## Referências relacionadas

- `specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md`: épico pai; este item é a fatia 2 da decomposição confirmada, incluindo regras de negócio, jornada, permissões, limites de upload e cenários de aceite já decididos naquele nível. Tipo: backlog relacionado (pai).
- `specs/completed/0008-fronteira-interna-pipeline-aplicacao/spec.md` (SPEC-0008, origem BACKLOG-0011): entrega a fachada síncrona `src/pipeline/service.py` (`run_pipeline`, `sync_vector_store`, `validate_retrieval`, `query_base`) e o teste estático de fronteira que `src/app/` deve respeitar. Tipo: spec relacionada (pré-requisito concluído).
- `specs/completed/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md` (SPEC-0009, origem BACKLOG-0012): remove a dívida de `.env` carregado no import de `config.py`, condição bloqueante para `src/app/`. Tipo: spec relacionada (pré-requisito concluído).
- `specs/completed/0011-cobrir-comportamento-backend-real-qdrant/spec.md` (SPEC-0011, origem BACKLOG-0013): cobre o backend real do Qdrant por teste, condição bloqueante para incorporar o pipeline a um backend assíncrono. Tipo: spec relacionada (pré-requisito concluído).
- `specs/backlog/0006-validar-recuperacao-operacao.md`: já registra a intenção de que a validação vire "módulo Python reaproveitável pelo backend FastAPI do BACKLOG-0008". Tipo: backlog relacionado.
- `.specsfy/STACK.md`, seção "Decisões e observações do projeto": registra que o projeto-mãe prevê FastAPI, PostgreSQL, Procrastinate, Cloudflare R2, LangGraph, Next.js — até aqui como direção futura, não dependência atual. Este item passa a adotar a parte de backend dessa direção. Tipo: documentação relacionada.
- `.specsfy/DATABASE.md`, seção "Informações a guardar confirmadas": já registra o formato esperado de base de documentos, execução do pipeline e consulta de validação, com ownership por papel (owner/admin/member) e retenção. Tipo: documentação relacionada.
- `.specsfy/RULES.md`: contém a nota "Revisar esta regra se este componente passar a persistir usuários, tenants ou ownership por conta própria" — esta fatia é exatamente esse ponto de revisão. Tipo: documentação relacionada (dívida de atualização a executar durante a implementação).
- `output/base_exemplo/`: base Markdown já presente no repositório, candidata a "base preparada" de contingência citada no BACKLOG-0008. Tipo: evidência de código.

## Comportamento esperado

1. Um pacote `src/app/` (hoje só com `__init__.py`) recebe uma aplicação FastAPI que consome exclusivamente `src/pipeline/service.py`, nunca módulos internos de `src/pipeline/`.
2. O backend expõe operações para: enviar arquivos Markdown (upload) ou selecionar a base preparada de contingência para o projeto ativo; iniciar uma execução do pipeline sobre essa base; consultar estado, etapas e contagens (previstos/inseridos/mantidos/removidos) de uma execução; repetir uma execução que falhou; apagar uma base e seu conteúdo associado; e realizar uma consulta de validação sobre a base indexada.
3. Toda operação de processamento (`run_pipeline` + `sync_vector_store`) é agendada como tarefa assíncrona via Procrastinate (fila sobre PostgreSQL) e não bloqueia a requisição HTTP que a disparou; o chamador consulta o progresso por polling do estado persistido.
4. O estado de cada execução (situação, etapa alcançada, contagens, horários, erro seguro sem segredo, manifesto) é persistido em PostgreSQL, sobrevivendo à finalização da requisição HTTP e do processo que executou a tarefa.
5. Os arquivos Markdown enviados por upload são armazenados no Cloudflare R2, associados ao tenant e ao projeto ativo, para permitir reprocessamento e exclusão posterior.
6. Toda requisição autentica por um token estático de demonstração, emitido fora do fluxo da API, associado de antemão a `tenant_id`, `project_id` e `role=owner`. Não há endpoint de login, cadastro ou convite nesta fatia.
7. O backend aplica o isolamento por tenant/projeto e as permissões por papel (owner e admin administram; member acompanha e consulta sem apagar) em cada operação, reaproveitando o escopo lógico `project_id`/`tenant_id` já existente na fachada e nos providers.
8. Repetir o processamento da mesma base, inclusive após falha, permanece idempotente: nenhum ponto duplicado é criado no vector store, respeitando a garantia já entregue por `sync_vector_store`.

## Regras de negócio

- `src/app/` importa somente `src/pipeline/service.py`; qualquer import de módulo interno de `src/pipeline/` é um erro de fronteira, coberto pelo teste estático já existente desde a SPEC-0008.
- Cada envio aceita até 50 arquivos `.md` em UTF-8, 5 MB por arquivo e 50 MB no total; formato, codificação e tamanho são validados pelo backend antes de agendar qualquer execução, sem processamento parcial (regra herdada do BACKLOG-0008).
- Owner e admin podem enviar, processar, repetir e apagar bases e execuções; member pode acompanhar e consultar, sem apagar (regra herdada do BACKLOG-0008 e de `.specsfy/DATABASE.md`).
- Apagar uma base remove seu conteúdo, execuções, consultas, chunks e vetores associados, preservando somente um registro sem conteúdo de que a exclusão ocorreu.
- O token estático de demonstração não é uma credencial de produção: não substitui a autenticação completa prevista para o projeto-mãe e não deve ser tratado como modelo final de autenticação.
- A tarefa assíncrona nunca lê `config.yaml` nem variável de ambiente por conta própria: a configuração resolvida chega até ela pelos mesmos parâmetros já exigidos pela fachada.
- Nenhum segredo (credencial de embeddings, Qdrant, Postgres, R2 ou o token estático) é retornado em resposta de API, persistido em texto livre de erro ou incluído no estado exposto ao frontend.

## Critérios de aceitação

```gherkin
Scenario: Iniciar uma execução sem bloquear a requisição
  Given uma base Markdown enviada ou selecionada como contingência para o projeto ativo
  When o owner inicia o processamento pela API
  Then a API responde imediatamente com o identificador da execução agendada
  And a tarefa assíncrona processa a base via Procrastinate sem manter a requisição HTTP aberta até o fim

Scenario: Acompanhar estado e contagens de uma execução
  Given uma execução em andamento agendada pela API
  When o frontend consulta o estado dessa execução
  Then a resposta traz a etapa alcançada e as contagens de previstos, inseridos, mantidos e removidos
  And os valores são lidos da persistência em PostgreSQL, não de estado em memória do processo

Scenario: Repetir uma execução que falhou sem duplicar
  Given uma execução registrada como falha em uma etapa
  When owner ou admin aciona a repetição pela API
  Then uma nova execução processa a mesma base do início
  And nenhum ponto duplicado é criado no vector store configurado

Scenario: Aplicar tenant, projeto e papel a cada requisição
  Given um token estático de demonstração associado a tenant_id, project_id e role=owner
  When uma requisição chega sem esse token ou com um token não reconhecido
  Then a API rejeita a requisição antes de tocar pipeline, persistência ou armazenamento de arquivo

Scenario: Rejeitar upload fora dos limites
  Given um envio com mais de 50 arquivos, arquivo maior que 5 MB, total maior que 50 MB ou extensão diferente de .md
  When o owner tenta iniciar o processamento desse envio
  Then a API identifica o problema e recusa o agendamento
  And nenhuma tarefa assíncrona é criada para esse envio

Scenario: Consultar a base indexada
  Given uma execução concluída com sucesso e sincronizada no vector store
  When alguém com acesso ao projeto envia uma consulta pela API
  Then a resposta traz o resultado recuperado e os chunks-fontes que o sustentam

Scenario: Impedir import indevido da fronteira interna
  Given um módulo novo em src/app/
  When esse módulo importa algo de src/pipeline/ que não seja src/pipeline/service.py
  Then o teste estático de fronteira falha e identifica o import proibido
```

## Qualidades e operação

- Segurança: token estático validado em toda requisição antes de qualquer acesso a pipeline, banco ou armazenamento; nenhum segredo (Postgres, R2, Qdrant, embeddings, token) é exposto em resposta, log ou estado persistido.
- Privacidade: apagar uma base remove arquivos no R2, execuções e consultas no Postgres, chunks e vetores no vector store, preservando somente um registro mínimo da exclusão, sem conteúdo.
- Desempenho e volume: a requisição de início de processamento responde antes da conclusão do pipeline; o volume por envio permanece limitado a 50 arquivos, 5 MB por arquivo e 50 MB no total; a fila Procrastinate processa uma execução por vez por base para preservar a idempotência do `sync_vector_store`.
- Auditoria e observabilidade: cada execução persiste etapa, contagens, horários de início e término e erro seguro; o manifesto de auditoria já produzido pela fachada fica acessível pelo retorno da API, não apenas em arquivo local.

## Dependências

- BACKLOG-0011 / SPEC-0008, concluída: fornece a fachada síncrona `src/pipeline/service.py` e o teste estático de fronteira que este item consome e estende.
- BACKLOG-0012 / SPEC-0009, concluída: remove a dívida do `.env` carregado no import, pré-requisito bloqueante já resolvido.
- BACKLOG-0013 / SPEC-0011, concluída: cobre os backends reais de vector store por teste, pré-requisito bloqueante já resolvido.
- Infraestrutura nova exigida por esta fatia: instância PostgreSQL, fila Procrastinate sobre esse mesmo Postgres, e bucket Cloudflare R2 — nenhuma delas existe hoje neste repositório.
- BACKLOG-0008, fatia 3: o frontend demonstrável consome a API entregue por este item; não pode iniciar antes dele.

## Situações de erro

- Token ausente ou não reconhecido: a API recusa a requisição antes de qualquer acesso a pipeline, Postgres ou R2.
- Upload fora dos limites de quantidade, tamanho, extensão ou codificação: a API identifica cada problema e não agenda processamento parcial.
- Falha em qualquer etapa do pipeline (carregamento, chunking, embeddings, indexação): a execução registra a etapa alcançada e uma mensagem de erro sem segredo; a primeira entrega não retoma automaticamente da etapa interrompida.
- Indisponibilidade do provider de embeddings, do vector store, do Postgres ou do R2: a execução falha de forma visível no estado persistido, sem expor credencial ou detalhe interno do provedor.
- Repetição de execução: sempre idempotente, mesmo repetida várias vezes após falhas sucessivas.

## Escopo

- Dentro: pacote `src/app/` com aplicação FastAPI; endpoints para upload de Markdown, seleção da base preparada, início de execução, consulta de estado/contagens/erros, repetição de execução, exclusão de base e consulta de validação; tarefa assíncrona via Procrastinate sobre PostgreSQL; persistência de execuções, contagens e consultas em PostgreSQL; armazenamento dos arquivos Markdown enviados em Cloudflare R2; autenticação por token estático de demonstração com tenant/projeto/papel associados; aplicação de permissões por papel (owner, admin, member).
- Fora: telas e componentes de frontend (fatia 3); cadastro, convite, login real e administração completa de usuários e papéis; ingestão multiformato (Fase 1, fora deste componente); novos backends de vector store além do Qdrant; qualquer mudança na lógica interna do pipeline já entregue por `src/pipeline/`.

## Dúvidas, decisões e riscos

- Decisão confirmada na Pergunta 1: adotar agora a stack alvo do projeto-mãe para esta fatia — PostgreSQL para persistência, Procrastinate (fila sobre o mesmo Postgres) para a execução assíncrona, e Cloudflare R2 para os arquivos Markdown enviados. Justificativa: `.specsfy/STACK.md` já declarava essa direção como destino futuro; adotá-la agora evita retrabalho quando a integração final acontecer.
- Decisão confirmada na Pergunta 2: a conta owner interna se autentica por um token estático de demonstração, configurado fora do fluxo da API e associado a `tenant_id`, `project_id` e `role=owner`. Não há tela de login nem tabela de usuários nesta fatia; cadastro e autenticação completa continuam fora de escopo, herdado do BACKLOG-0008.
- Risco registrado: esta é a primeira vez que o componente persiste dados próprios além de arquivos locais (manifesto, chunks.json) — `.specsfy/RULES.md` já sinaliza que a regra sobre `tenant_id` como "somente chave de escopo lógico, sem tabela própria" precisa ser revisada quando isso acontecer. A implementação desta fatia deve atualizar essa regra.
- Risco registrado: introduzir PostgreSQL, Procrastinate e Cloudflare R2 de uma vez aumenta a superfície de infraestrutura da demonstração; a especificação executável (SPEC) deve detalhar provisionamento mínimo viável (local via Docker Compose, por exemplo) sem transformar isso em decisão de deploy de produção.
- Risco herdado do BACKLOG-0011: a fachada pode virar um repasse fino se a API só reexportar as quatro operações sem agregar o valor de estado/contagens assíncronas; a especificação deve declarar os endpoints pelo caso de uso observável (iniciar, acompanhar, repetir, apagar, consultar), não pela função interna que cada um chama.
- Nenhuma lacuna aplicável permanece no nível deste item; detalhes de schema, rotas exatas e formato de payload pertencem à especificação executável.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Brief pronto para especificar

1. **Problema e objetivo:** o pipeline só é operável por CLI síncrona; esta fatia cria o contrato FastAPI, a tarefa assíncrona e a persistência para que um frontend possa disparar e acompanhar o pipeline.
2. **Atores:** Marcio como `owner`; `admin` administra bases e execuções; `member` acompanha e consulta sem apagar.
3. **Escopo:** `src/app/` com FastAPI, upload/seleção de base, início e acompanhamento de execução, repetição, exclusão e consulta — tudo sobre a fachada `src/pipeline/service.py`, com Postgres, Procrastinate e Cloudflare R2 como infraestrutura nova.
4. **Fora de escopo:** frontend (fatia 3), cadastro/login completo, ingestão multiformato, novos backends de vector store, mudança na lógica interna do pipeline.
5. **Jornadas e regras essenciais:** enviar ou selecionar base → agendar execução assíncrona → acompanhar estado/contagens → repetir se falhar → apagar quando autorizado → consultar a base indexada; tudo isolado por tenant/projeto e papel, autenticado por token estático de demonstração.
6. **Aceite:** oito cenários Given/When/Then cobrindo execução não bloqueante, acompanhamento por persistência real, repetição idempotente, autenticação obrigatória, limites de upload, consulta e fronteira de import.
7. **Restrições técnicas:** `src/app/` só importa `src/pipeline/service.py` (teste estático já existente); nenhuma leitura de `config.yaml`/env fora dos entrypoints; nenhum segredo exposto; idempotência do `sync_vector_store` preservada.
8. **Suposições confirmadas:** BACKLOG-0011/0012/0013 concluídos; `output/base_exemplo/` como candidata a base preparada; token estático como autenticação suficiente para esta fatia.
9. **Decisões abertas:** nenhuma no nível do item. Schema exato de persistência, rotas HTTP, formato de payload e provisionamento mínimo de Postgres/R2 ficam para a especificação executável.

## Próximo passo

Promovido em 2026-09-04 para `specs/draft/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md` (SPEC-0012).
A partir daqui, a SPEC-0012 é a fonte normativa; este backlog preserva apenas a
proveniência e as decisões do refinamento.
