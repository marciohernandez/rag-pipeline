# Perfil de interação do Specsfy

Este arquivo guarda somente o nível de conhecimento e as respostas confirmadas
durante o setup. Ele orienta a forma da conversa e não substitui `PROJECT.md`,
`STACK.md`, `RULES.md`, `DATABASE.md`, `INTERFACE.md`, `DESIGNSYSTEM.MD` ou uma
spec.

## Nível de conhecimento

| Campo | Valor |
| --- | --- |
| Nível atual | intermediário |
| Fonte da confirmação | Conversa atual: pessoa em processo de aprendizado, com conhecimentos e decisões prévias em algumas áreas |
| Última confirmação | 2026-08-31 |

Valores permitidos: `iniciante`, `intermediário` e `experiente`.

## Respostas confirmadas

Registre somente respostas dadas pela pessoa ou declarações inequívocas já
presentes nas fontes lidas. Não registre segredos, tokens, senhas ou dados de
produção.

| Área | Pergunta ou assunto | Resposta normalizada | Fonte | Confirmado em | Alcance |
| --- | --- | --- | --- | --- | --- |
| Interação | Profundidade das orientações | Nível intermediário, com explicações curtas nas escolhas conhecidas e aprofundamento adaptativo em assuntos novos | Conversa atual | 2026-08-31 | Todo o setup e conversas posteriores do Specsfy |
| Contexto do projeto | Relação com outro projeto | Este repositório é parte de um projeto maior que já possui constituição e decisões sobre a forma de desenvolvimento; essas fontes devem ser consultadas antes de consolidar regras locais | Conversa atual | 2026-08-31 | Arquitetura, regras e processo de desenvolvimento deste componente |
| Contexto do projeto | Consolidação em repositório mãe | O repositório `rag-pipeline` agora consolida ambas as fases: ingestão multi-formato (Fase 1) e indexação vetorial (Fase 2). A integração em um único repo simplifica a stack, evita duplicação e facilita testes E2E | Conversa atual | 2026-09-03 | Propósito duplo: entrega de Markdown e transformação em coleções vetoriais |
| Contexto do projeto | Fontes normativas externas | A pessoa fornecerá a constituição, o briefing e a tech stack do `rag-pipeline` para orientar este componente | Conversa atual | 2026-08-31 | Setup e decisões futuras; preservar a raiz confirmada do componente |
| Processo de desenvolvimento | Isolamento por branch | Substituída em 2026-09-07 pela regra precisa de `.specsfy/RULES.md`: branch por unidade de integração — `spec/<NNNN>-<slug>` para uma única spec, `chore/<slug>` para tooling, CI e documentação, `fix/<slug>` para correção fora de spec; uma branch nunca carrega duas specs; não existe branch de milestone, que fecha por tag anotada em `main`. A formulação anterior por "fase" era ambígua e permitiu acumular cinco specs em uma branch | Conversa atual (2026-09-03), revisada pela auditoria de 2026-09-07 | 2026-09-07 | Repositório unificado `rag-pipeline` com Specsfy como workflow normativo |
| Produto | Objetivo do projeto-mãe | O `rag-pipeline` prepara e valida bases de conhecimento: ingere fontes heterogêneas, extrai um Markdown por documento, detecta contradições, recebe validação humana e entrega Markdown limpo | `rag-pipeline/briefing.md` fornecido na conversa | 2026-08-31 | Projeto-mãe; orientação de integração deste componente |
| Produto | Escopo consolidado | O `rag-pipeline` agora cobre: Fase 1 (ingestão multi-formato → Markdown) + Fase 2 (Markdown → chunks → embeddings → Qdrant). Modularizado em `src/ingestion/` e `src/indexing/` com contratos neutros | Conversa atual e código local | 2026-09-03 | Repositório unificado; testes E2E; integração com futuros componentes de IA |
| Pessoas e acesso | Público inicial do projeto-mãe | Uso interno por Marcio e equipe de consultoria; o projeto-mãe é multi-tenant desde a V1 e prevê `owner`, `admin` e `member`, sem `viewer` | `rag-pipeline/briefing.md` e constituição 1.2.1 | 2026-08-31 | Projeto-mãe; não implica autenticação já existente neste componente CLI |
| Arquitetura | Fontes normativas do projeto-mãe | Constituição 1.2.1 prevalece; `briefing.md` detalha produto e `tech_stack.md` detalha implementação. Conflitos devem seguir a constituição | Arquivos fornecidos na conversa | 2026-08-31 | Decisões futuras de integração; stack implementada localmente continua evidenciada pelo código |
| Processo de desenvolvimento | Workflow normativo | Usar Specsfy como workflow canônico do `rag-pipeline`; preservar os princípios arquiteturais (LangChain-first, modular, testável) da constituição do projeto-mãe | Conversa atual e `.specsfy/Spec.md` | 2026-09-03 | Specs, gates, tarefas, testes, implementação e tracking via Specsfy |
| Tracking | Reinício no Linear | A estrutura atual do Linear praticamente não foi utilizada e pode ser recomeçada para acompanhar o `RAG Pipeline SaaS` a partir do Specsfy | Conversa atual | 2026-08-31 | Projetos, milestones e issues do produto no Linear; destino da estrutura antiga ainda pendente |
| Tracking | Destino do projeto antigo no Linear | Projeto antigo renomeado para `LEGADO — RAG Pipeline SaaS — Curadoria de Base de Conhecimento (SpecKit)` e marcado como cancelado; 85 issues e seis milestones foram preservadas | Conversa atual e Linear (`527b0fa8-4889-4d3d-8fc4-902e8a7c7fef`) | 2026-08-31 | Histórico anterior, somente referência |
| Tracking | Novo projeto no Linear | Projeto vazio `RAG Pipeline SaaS` criado na equipe `LeadMedia`, em Backlog, para acompanhamento orientado pelo Specsfy | Conversa atual e Linear (`f9f08477-26cb-4ffe-829b-336913413d18`) | 2026-08-31 | Tracking novo do produto e seus componentes |
| Tracking | Representação do componente atual | O `rag-ingestion-pipeline` é o milestone `M0 — Finalizar o componente rag-ingestion-pipeline` no novo projeto `RAG Pipeline SaaS`; sua conclusão exige estabilidade, testes, documentação e preparação para integração futura | Conversa atual e Linear (`edffbec3-8407-4c77-993f-da87f60fdde1`) | 2026-08-31 | Primeira fase do tracking novo; sem antecipar o MVP de curadoria |
| Tracking | Formação do backlog do M0 | Auditar código, testes e documentos existentes e propor somente trabalho realmente pendente; não converter planos históricos sem conferir a implementação | Conversa atual | 2026-08-31 | Backlogs Specsfy e issues Linear do milestone M0 |
| Tracking | Estratégia inicial do backlog M0 | Criar os sete itens auditados no Specsfy e no Linear, aprofundar primeiro somente o BACKLOG-0001 e manter os demais capturados até sua vez de refinamento | Conversa atual, opção 1 escolhida | 2026-08-31 | BACKLOG-0001 a BACKLOG-0007 e issues LEAD-86 a LEAD-92 |
| Testes e operação | Critério de "pronto" do milestone M0 | Ruff e Pytest verdes localmente e em CI a cada push da branch de fase, somados a logs estruturados de execução com escopo lógico e contagens de pontos previstos, inseridos, mantidos e removidos, sem expor segredos. APM, tracing distribuído e métricas externas ficam fora, como escopo do projeto-mãe | Conversa atual, recomendação aceita na opção 1 | 2026-08-31 | Critério de conclusão do M0; insumo para BACKLOG-0001, BACKLOG-0006 e BACKLOG-0007 |
| Processo de desenvolvimento | Reconstrução da documentação no setup | Pular o `$specsfy-documentator` quando `build_documentation --check` retornar exit 0 e não houver commit novo desde a última reconstrução; a obrigatoriedade permanece ao fim de cada tarefa de implementação | Conversa atual, opção 1 escolhida | 2026-09-15 | Execuções do `$specsfy-setup` neste repositório |

## Uso pelo setup

Decisão confirmada em 2026-10-05 na conversa: resposta “1” significa círculo
junto da ação ou área em processamento, mantendo o restante da tela
disponível. Alcance: SPEC-0025, feedback de carregamento nas telas existentes.

- Antes de perguntar, leia este arquivo, a conversa atual e os contextos do
  projeto disponíveis.
- Uma resposta já registrada ou explicitamente declarada em outra fonte não
  volta a ser perguntada.
- Se fontes divergirem, pergunte apenas para resolver a divergência e registre
  a nova fonte e o alcance da resposta.

## Decisão de refinamento — 2026-10-05

Fonte: conversa atual, resposta literal “1” à organização do trabalho de
ingestão. Resposta normalizada: ampliar BACKLOG-0025 com o fluxo completo
inspirado nos Document Stores do Flowise, preservando o item existente.
Alcance: refinamento do backlog de ingestão; não confirma conexões, providers
novos, modelo de dados ou composição ainda não discutidos.

## Conexões para ingestão — 2026-10-05

Fonte: conversa atual, resposta literal “1” à configuração das conexões
de embeddings e Qdrant. Resposta normalizada: cadastrar conexões
reutilizáveis pela interface e selecioná-las na etapa de upsert.
Alcance: BACKLOG-0025; compartilhamento, permissões, campos e ciclo de vida
ainda não confirmados.

## Compartilhamento das conexões — 2026-10-05

Fonte: conversa atual, resposta literal “1” à reutilização de conexões.
Resposta normalizada: owner/admin da mesma equipe e projeto podem reutilizar
conexões em qualquer Workspace. Alcance: BACKLOG-0025; não confirma acesso
ao segredo, permissões de edição/exclusão ou ciclo de vida.

## Ciclo de vida das conexões — 2026-10-05

Fonte: conversa atual, resposta literal “1” sobre retirar conexões em uso.
Resposta normalizada: desativar preservando vínculos e histórico; exigir
conexão ativa no próximo upsert; permitir exclusão definitiva somente sem
uso. Alcance: BACKLOG-0025; permissões de gestão e edição ainda em descoberta.

## Administração das conexões — 2026-10-06

Fonte: conversa atual, resposta literal “1” sobre quem administra conexões.
Resposta normalizada: owner e admin cadastram, editam, desativam e excluem
qualquer conexão da equipe e projeto, sem distinção de autoria; member não
administra. Alcance: BACKLOG-0025; segredos, campos e auditoria ainda abertos.

## Segredos das conexões — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: segredo
somente escrita; a interface e a API nunca devolvem a chave (apenas forma
mascarada); trocar exige nova chave; armazenamento cifrado no servidor.
Alcance: BACKLOG-0025; campos não secretos e auditoria ainda abertos.

## Tipos de conexão — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: primeira
entrega com embeddings OpenAI (modelo e URL base opcionais) e Qdrant; sem
Chroma, Pinecone nem outros providers. Alcance: BACKLOG-0025; Record Manager,
dimensões e auditoria ainda abertos.

## Dimensão dos vetores — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: bloquear o
upsert antes de gravar quando a dimensão do modelo divergir da coleção, com
mensagem clara. Alcance: BACKLOG-0025; origem da dimensão e Record Manager
ainda abertos.

## Record Manager — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: sem etapa
nem conexão de Record Manager; o upsert reaproveita a sincronização da
SPEC-0002 e a interface mostra inseridos, mantidos e removidos. Alcance:
BACKLOG-0025.

## Prévia e chunks — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: prévia
descartável sem persistência; aprovar gera e publica; sem edição/exclusão de
chunks individuais. Alcance: BACKLOG-0025. Ciclo de Dados/Integrações
encerrado por limite de oito perguntas; lacunas registradas no backlog.

## Interface: fluxo de ingestão — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: página
própria com etapas (Arquivos → Divisão → Prévia → Publicação), aberta a
partir do Workspace. Alcance: BACKLOG-0025, área Interface (pergunta 1 de 8).

## Interface: destino do UploadBaseSheet — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: página com
etapas substitui o `UploadBaseSheet`; "Usar base preparada" vira opção da
etapa Arquivos; sem envio com execução completa imediata. Alcance:
BACKLOG-0025, Interface (pergunta 2 de 8).

## Interface: gestão de conexões — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: item de
menu "Conexões" só para owner/admin, DataGrid + Sheet como em Pessoas.
Alcance: BACKLOG-0025, Interface (pergunta 3 de 8).

## Interface: etapa Divisão — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: splitter,
tamanho e overlap com padrões do `config.yaml`, validação em linha, aviso dos
arquivos Q&A; sem avançado nem configuração por arquivo. Alcance:
BACKLOG-0025, Interface (pergunta 4 de 8).

## Interface: etapa Prévia — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: resumo com
contagens e avisos, lista paginada de chunks com filtro por documento,
somente leitura. Alcance: BACKLOG-0025, Interface (pergunta 5 de 8).

## Interface: etapa Publicação — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: seletores
de conexões ativas, dimensões em linha, coleção, resumo final, Publicar
bloqueado com razão visível, destino na Base com PainelProgresso; sem testar
conexão. Alcance: BACKLOG-0025, Interface (pergunta 6 de 8).

## Interface: saída e retorno — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: sem
persistência no servidor antes de publicar; voltar preserva o preenchido;
sair ou recarregar descarta, com aviso. Alcance: BACKLOG-0025, Interface
(pergunta 7 de 8).

## Interface: estados e acessibilidade — 2026-10-06

Fonte: conversa atual, resposta literal “1”. Resposta normalizada: conjunto
completo (loading, vazio, erro, permissão, teclado, responsivo) no fluxo e
em Conexões. Alcance: BACKLOG-0025, Interface (pergunta 8 de 8). Área de
Interface encerrada por limite; lacunas registradas no backlog.

## Decisões de refinamento — SPEC-0026 — 2026-10-06

Fonte: conversa atual, respostas literais “1” às três perguntas de fechamento
das pendências do BACKLOG-0025. Alcance: SPEC-0026.

- Auditoria das conexões: histórico próprio sem a chave, retenção de 90 dias.
- Chave de cifra: única, via secret do Swarm ou variável de ambiente, sem
  rotação automática; trocar exige recadastrar as conexões.
- Limites de divisão: tamanho de 200 a 4000; overlap de 0 até a metade do
  tamanho, sempre menor que o tamanho.
