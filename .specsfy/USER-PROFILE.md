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
| Contexto do projeto | Projeto-mãe e sequência de entrega | O projeto-mãe chama-se `rag-pipeline` e ainda está em estágio inicial. O `rag-ingestion-pipeline` é o primeiro componente a ser finalizado; depois, deverá ficar preparado para integração e continuidade do produto completo | Conversa atual | 2026-08-31 | Finalidade, limites, arquitetura e preparação para integração |
| Contexto do projeto | Fontes normativas externas | A pessoa fornecerá a constituição, o briefing e a tech stack do `rag-pipeline` para orientar este componente | Conversa atual | 2026-08-31 | Setup e decisões futuras; preservar a raiz confirmada do componente |
| Processo de desenvolvimento | Isolamento por fase | Cada fase de desenvolvimento deve ser realizada em uma branch própria, sem trabalhar diretamente na branch principal | Conversa atual | 2026-08-31 | Repositório `rag-ingestion-pipeline` e preparação futura do projeto completo |
| Produto | Objetivo do projeto-mãe | O `rag-pipeline` prepara e valida bases de conhecimento: ingere fontes heterogêneas, extrai um Markdown por documento, detecta contradições, recebe validação humana e entrega Markdown limpo | `rag-pipeline/briefing.md` fornecido na conversa | 2026-08-31 | Projeto-mãe; orientação de integração deste componente |
| Produto | Papel deste componente | O `rag-ingestion-pipeline` cobre chunking, embeddings, indexação vetorial e validação de recuperação; deve ser finalizado separadamente e preparado para integração futura, sem antecipar o escopo V1 do projeto-mãe | Conversa atual, código local e `rag-pipeline/briefing.md` | 2026-08-31 | Repositório atual e integração futura V2 |
| Pessoas e acesso | Público inicial do projeto-mãe | Uso interno por Marcio e equipe de consultoria; o projeto-mãe é multi-tenant desde a V1 e prevê `owner`, `admin` e `member`, sem `viewer` | `rag-pipeline/briefing.md` e constituição 1.2.1 | 2026-08-31 | Projeto-mãe; não implica autenticação já existente neste componente CLI |
| Arquitetura | Fontes normativas do projeto-mãe | Constituição 1.2.1 prevalece; `briefing.md` detalha produto e `tech_stack.md` detalha implementação. Conflitos devem seguir a constituição | Arquivos fornecidos na conversa | 2026-08-31 | Decisões futuras de integração; stack implementada localmente continua evidenciada pelo código |
| Processo de desenvolvimento | Workflow normativo deste componente | Usar Specsfy como workflow canônico do `rag-ingestion-pipeline`; preservar os princípios arquiteturais da constituição do projeto-mãe sem criar artefatos paralelos do SpecKit neste repositório | Conversa atual | 2026-08-31 | Specs, gates, tarefas, testes, implementação e tracking no Linear deste componente |
| Tracking | Reinício no Linear | A estrutura atual do Linear praticamente não foi utilizada e pode ser recomeçada para acompanhar o `RAG Pipeline SaaS` a partir do Specsfy | Conversa atual | 2026-08-31 | Projetos, milestones e issues do produto no Linear; destino da estrutura antiga ainda pendente |
| Tracking | Destino do projeto antigo no Linear | Projeto antigo renomeado para `LEGADO — RAG Pipeline SaaS — Curadoria de Base de Conhecimento (SpecKit)` e marcado como cancelado; 85 issues e seis milestones foram preservadas | Conversa atual e Linear (`527b0fa8-4889-4d3d-8fc4-902e8a7c7fef`) | 2026-08-31 | Histórico anterior, somente referência |
| Tracking | Novo projeto no Linear | Projeto vazio `RAG Pipeline SaaS` criado na equipe `LeadMedia`, em Backlog, para acompanhamento orientado pelo Specsfy | Conversa atual e Linear (`f9f08477-26cb-4ffe-829b-336913413d18`) | 2026-08-31 | Tracking novo do produto e seus componentes |
| Tracking | Representação do componente atual | O `rag-ingestion-pipeline` é o milestone `M0 — Finalizar o componente rag-ingestion-pipeline` no novo projeto `RAG Pipeline SaaS`; sua conclusão exige estabilidade, testes, documentação e preparação para integração futura | Conversa atual e Linear (`edffbec3-8407-4c77-993f-da87f60fdde1`) | 2026-08-31 | Primeira fase do tracking novo; sem antecipar o MVP de curadoria |
| Tracking | Formação do backlog do M0 | Auditar código, testes e documentos existentes e propor somente trabalho realmente pendente; não converter planos históricos sem conferir a implementação | Conversa atual | 2026-08-31 | Backlogs Specsfy e issues Linear do milestone M0 |
| Tracking | Estratégia inicial do backlog M0 | Criar os sete itens auditados no Specsfy e no Linear, aprofundar primeiro somente o BACKLOG-0001 e manter os demais capturados até sua vez de refinamento | Conversa atual, opção 1 escolhida | 2026-08-31 | BACKLOG-0001 a BACKLOG-0007 e issues LEAD-86 a LEAD-92 |

## Uso pelo setup

- Antes de perguntar, leia este arquivo, a conversa atual e os contextos do
  projeto disponíveis.
- Uma resposta já registrada ou explicitamente declarada em outra fonte não
  volta a ser perguntada.
- Se fontes divergirem, pergunte apenas para resolver a divergência e registre
  a nova fonte e o alcance da resposta.
