# Contexto de continuação: estruturação do projeto-mãe

Atualizado em 2026-09-03.

## Objetivo deste documento

Este arquivo serve como handoff para outro modelo ou desenvolvedor continuar o trabalho sem depender do histórico da conversa. Ele resume o estado do repositório, as decisões já tomadas e o próximo trabalho recomendado.

## Estado atual do repositório

- Repositório: `https://github.com/marciohernandez/rag-pipeline.git`
- Branch atual: `main`
- Worktree: limpo e sincronizado com `origin/main`
- Último merge: `8589c4e Merge branch 'chore/rename-parent-repo'`
- Renomeação concluída: o projeto deixou de usar `chunk`/`rag-ingestion-pipeline` como identidade principal e passou a usar `rag-pipeline`.
- Ambiente: `.venv` recriado com `uv sync --dev`.
- Validação: `238 passed`; `uv run ruff check .` aprovado sem aviso após a migração da configuração do Ruff.

## O que foi consolidado

O repositório agora reúne duas fases:

1. Fase 1: ingestão, extração, curadoria e geração de Markdown.
2. Fase 2: chunking, embeddings, indexação vetorial e validação da recuperação.

O código existente é principalmente um pipeline Python operado por CLI. As principais superfícies são:

- `pipeline.py`
- `upsert_from_chunks.py`
- `search.py`
- `chat.py`
- `validate.py`
- módulos em `src/`, incluindo loader, chunker, identity, manifest, quality, validation, safety, indexing e providers.

O pipeline atual já possui providers neutros para embeddings e vector stores, suporte a Qdrant, ChromaDB e Pinecone, manifesto, qualidade, validação de recuperação e política fail-closed.

## Decisão arquitetural principal

A consolidação do nome do repositório não significa que o produto completo do projeto-mãe já esteja implementado.

A decisão registrada é de consolidação gradual:

1. Finalizar e validar o componente atual.
2. Incorporar o pipeline ao backend do projeto-mãe como módulo interno.
3. Criar o frontend demonstrável no mesmo projeto-mãe.
4. Arquivar o repositório separado somente depois de validar a migração.

Durante a transição, o histórico deve ser preservado e rollback deve continuar possível.

## O que ainda não existe

Ainda não foram implementados neste repositório:

- backend FastAPI;
- API HTTP para upload, execução, estado, contagens, erros e consulta;
- execução assíncrona por tarefas;
- persistência própria para bases, execuções, etapas, consultas e auditoria;
- frontend Next.js;
- autenticação, tenant/projeto/roles no backend do produto;
- telas de projeto e detalhe da execução.

A interface atual continua sendo CLI. `INTERFACE.md` e `docs/frontend.md` registram que não há interface para pessoas implementada.

## Fontes importantes

### Projeto e arquitetura

- `PROJECT.md`: visão, capacidades, limites e contexto técnico.
- `docs/architecture.md`: arquitetura Python atual e fronteiras dos módulos.
- `docs/application.md`: superfícies operacionais existentes.
- `docs/flows.md`: fluxos CLI.
- `INTERFACE.md`: estado atual da interface e direção futura.
- `DESIGNSYSTEM.MD`: regras globais para futura interface.

### Planejamento

- `specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md`: backlog principal para concluir o pipeline e entregar demonstração no projeto-mãe.
- `specs/backlog/0011-contrato-handoff-projeto-mae.md`: backlog para definir o contrato de integração/handoff; ainda está `Captured` e não refinado.
- `specs/milestones/M01.md`: milestone atual, com as specs 0001 a 0007 concluídas e backlogs relacionados ainda pendentes.
- `specs/completed/0001...` até `0007...`: specs já concluídas do componente.

## Diferença entre BACKLOG-0008 e BACKLOG-0011

### BACKLOG-0008

É o épico estrutural e funcional. Descreve:

- conclusão comprovada do fluxo Markdown -> chunks -> embeddings -> indexação -> recuperação;
- incorporação posterior ao backend do `rag-pipeline`;
- interface Python estável;
- FastAPI;
- tarefa assíncrona;
- persistência;
- frontend demonstrável;
- duas telas principais: Projeto e Detalhe da execução;
- upload de arquivos Markdown ou uso de base preparada;
- acompanhamento de etapas e contagens;
- consulta com chunks-fontes;
- repetição idempotente de falhas;
- limites de upload, tenant, projeto e permissões.

O próprio backlog diz que as fatias 2 e 3 devem receber backlogs e specs no projeto-mãe depois que a raiz do projeto-mãe for confirmada.

### BACKLOG-0011

Não é a estruturação completa do projeto. É o contrato de handoff entre o pipeline e o projeto-mãe. Deve declarar, para os mantenedores da integração:

- interface Python estável;
- pontos de entrada;
- configuração exigida;
- limites;
- dívidas conhecidas;
- o que pode e não pode ser consumido.

Ele ainda precisa de refinamento. As dúvidas abertas são formato do contrato, assinatura da interface, dívidas que devem ser declaradas e confirmação da raiz responsável.

## Contrato já implementado para entrada do projeto-mãe

A SPEC-0002, já concluída, implementou parte do contrato de recebimento de Markdown:

- `document_id` do frontmatter tem precedência sobre a identidade determinística;
- `tenant_id` pode participar do escopo lógico e a sincronização é fail-closed quando há inconsistência;
- `status` bloqueado pode excluir documento antes do chunking por configuração;
- `type` e `version` são preservados como metadados;
- `splitter: qa` divide o corpo por `++++`, mantendo cada par em um chunk;
- documentos atuais sem frontmatter continuam compatíveis.

Isso é um contrato de entrada de dados, não ainda o contrato completo de integração da aplicação.

## Direção de produto para a demonstração

A jornada mínima definida no BACKLOG-0008 é:

1. Marcio acessa o contexto de um projeto como `owner`.
2. Envia vários arquivos `.md` UTF-8 ou escolhe uma base preparada.
3. O backend valida os limites antes de agendar a execução.
4. Uma tarefa assíncrona executa o pipeline.
5. O frontend mostra estado, etapas, documentos, chunks previstos, inseridos, mantidos e removidos.
6. Marcio consulta a base indexada.
7. A tela mostra o resultado e os chunks-fontes recuperados.
8. Em caso de falha, a tentativa preserva etapa e erro seguro e pode ser repetida por `owner` ou `admin`.

Limites confirmados para upload:

- até 50 arquivos;
- somente `.md`;
- UTF-8;
- 5 MB por arquivo;
- 50 MB por envio;
- nenhuma execução parcial para envio inválido.

Telas previstas no frontend:

- Projeto: bases, execuções, upload e base preparada.
- Detalhe da execução: progresso, contagens, erro, repetição e consulta.

Stack futura prevista: FastAPI no backend; Next.js App Router, shadcn/ui, Tailwind e TanStack Query no frontend. Essa stack ainda não está implementada neste repositório.

## Próximo passo recomendado

O primeiro trabalho agora é fechar a definição da estrutura-alvo, antes de criar telas ou código de frontend:

1. Confirmar que a raiz do projeto-mãe é este repositório `rag-pipeline`.
2. Decidir quais diretórios representarão backend, domínio, tarefas, persistência, API e frontend.
3. Definir a fronteira entre o pipeline existente e o backend de aplicação.
4. Refinar o BACKLOG-0011 como contrato de integração interno.
5. Transformar a fatia de incorporação do BACKLOG-0008 em uma spec executável.
6. Só depois implementar a primeira fatia vertical: receber uma base Markdown, criar uma execução assíncrona, chamar o pipeline e consultar o estado.

Não começar criando um frontend isolado. O frontend depende do contrato de execução, persistência, permissões e API.

## Cuidados para o próximo modelo

- Ler `AGENTS.md` e `.specsfy/Spec.md` antes de usar o fluxo Specsfy.
- Consultar `PROJECT.md`, `DESIGNSYSTEM.MD`, `.specsfy/STACK.md`, `.specsfy/RULES.md`, `.specsfy/DATABASE.md`, `.specsfy/PACKAGES.md` e `.specsfy/USER-PROFILE.md` antes de planejar alterações.
- O projeto usa uma fonte normativa por spec em `specs/<estado>/<id>-<slug>/spec.md`; não criar `plan.md`, `tasks.md` ou outra fonte paralela.
- Para refinar backlog, usar o fluxo de backlog; para criar spec, usar o fluxo de specify; para implementar, usar o fluxo de implement.
- Não apagar históricos nem substituir silenciosamente decisões já registradas.
- Verificar o estado do Git antes de editar. O ponto de partida esperado é `main` limpa e sincronizada.

## Resumo em uma frase

O `rag-pipeline` agora é o repositório principal consolidado, mas o trabalho seguinte é especificar e implementar sua estrutura de aplicação, começando pelo contrato interno e pela integração do pipeline Python com um backend FastAPI assíncrono, antes do frontend.
