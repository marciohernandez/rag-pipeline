# Banco de dados

Mapa de persistência do pipeline Python. Não inclui schemas internos de
dependências instaladas em `.venv`, pois eles pertencem aos fornecedores e não
ao domínio deste repositório.

## Fontes de dados

<!-- specsfy:database:start -->
| Fonte | Tecnologia/forma | Evidência |
| --- | --- | --- |
| Documentos de entrada | Arquivos Markdown com frontmatter YAML | `config.yaml`, `src/pipeline/loader.py` |
| Auditoria de chunks | Arquivo JSON local | `config.yaml`, `src/pipeline/exporter.py` |
| Manifesto de sincronização | Arquivo JSON local | `pipeline.py`, `src/pipeline/manifest.py` |
| Banco vetorial principal | Collection Qdrant remota, configurada sem credenciais no código | `config.yaml`, `src/pipeline/providers/vectorstores/qdrant.py` |
| Persistência do backend de aplicação | PostgreSQL (tabelas `workspaces`, `bases`, `executions`, `queries`) | `APP_DATABASE_URL`, `src/app/db.py`, `src/app/models.py`, `alembic/versions/0019_workspaces.py` (SPEC-0012, SPEC-0019) |
| Arquivos Markdown enviados pelo backend | Cloudflare R2 (S3-compatível) ou disco local de desenvolvimento | `src/app/storage.py` (`S3CompatibleStorage`, `LocalDirectoryStorage`) (SPEC-0012) |

## Estruturas detectadas

| Estrutura | Tipo | Campos | Relações | Fonte |
| --- | --- | --- | --- | --- |
| Documento Markdown | Arquivo de origem | `page_content`, frontmatter (`document_id`, `tenant_id`, `type`, `version`, `status`, `splitter`), `nome_arquivo`, `caminho_relativo`, `source_hash` | Origina um `document_id` e vários chunks | `src/pipeline/loader.py`, `src/pipeline/identity.py` |
| Chunk auditável | Item de `chunks.json` | `chunk_index`, `nome_arquivo`, `total_chunks`, `metadata`, `content`, `content_length` | Pertence a um documento; usa `chunk_id`, `document_id`, `project_id` e `tenant_id` opcional | `src/pipeline/exporter.py`, `src/pipeline/identity.py` |
| Manifesto de execução | Objeto JSON | `run_id`, `generated_at`, `project_id`, `collection_name`, embedding, contagens, documentos, `chunk_ids`, `excluded_by_status_count` | Consolida documentos e chunks esperados antes da indexação; conta exclusões por status | `src/pipeline/manifest.py`, `src/pipeline/status_gate.py` |
| Ponto Qdrant | Vetor + payload | ID=`chunk_id`, vetor configurado, `page_content`, `metadata` (inclui `tenant_id`, `type`, `version` quando presentes) | Escopo lógico por `metadata.project_id` + `metadata.tenant_id` quando declarado; documento por `metadata.document_id` | `src/pipeline/providers/vectorstores/qdrant.py` |
| Tabela `workspaces` | Tabela PostgreSQL | `id` (UUID textual), `tenant_id`, `project_id`, `nome`, `criado_em`, `apagada_em`; índice `ix_workspaces_tenant_project` | Agrupa várias `bases`; exclusão lógica; a API bloqueará exclusão enquanto houver Base ativa | `src/app/models.py`, `alembic/versions/0019_workspaces.py` (SPEC-0019) |
| Tabela `bases` | Tabela PostgreSQL | `id` (UUID textual), `tenant_id`, `project_id`, `workspace_id` (FK `NOT NULL`, índice `ix_bases_workspace_id`), `nome`, `origem` (`upload`\|`preparada`), `collection_name` (`NOT NULL`), `metadados_chunk` (JSON `NOT NULL`, server default `[]`), `documentos` (Integer, `NOT NULL`, `server_default 0` — contagem de arquivos recebidos na criação), `criado_em`, `apagada_em` | Pertence a um `Workspace`; tem várias `executions` e `queries`; `nome` é limpo na exclusão lógica | `src/app/models.py`; revisões `f3b60ce4f7f4` (documentos) e `0019_workspaces` (Workspace, coleção e metadados) |
| Tabela `executions` | Tabela PostgreSQL | `id` (UUID), `base_id` (FK), `situacao` (`pending`\|`running`\|`succeeded`\|`failed`), `etapa`, `previstos`, `inseridos`, `mantidos`, `removidos`, `erro`, `iniciado_em`, `concluido_em`. Índice único parcial `uq_executions_base_active` em `base_id`, filtrado por `situacao IN ('pending','running')` — garante no banco, atomicamente, no máximo uma execução ativa por base | Pertence a uma `Base`; removida quando a base é apagada | `src/app/models.py`; índice `uq_executions_base_active` adicionado pela SPEC-0015 (revisão Alembic `4d0fd0aa498e`) |
| Tabela `queries` | Tabela PostgreSQL | `id` (UUID), `base_id` (FK), `tenant_id`, `project_id`, `pergunta`, `resultado`, `chunks_fontes` (JSON), `criado_em` | Pertence a uma `Base`; removida quando a base é apagada | `src/app/models.py` (SPEC-0012) |
<!-- specsfy:database:end -->

Nota: ChromaDB e Pinecone foram removidos como providers concretos de vector
store pela SPEC-0010 (2026-09-04); Qdrant é hoje o único backend real, com a
abstração multi-provider mantida aberta em `src/pipeline/providers/` para
novos destinos futuros.

## Decisões, ownership e retenção

- A pasta Markdown configurada é a fonte de verdade da execução local.
- No Qdrant, `sync_mode: mirror` exige conjunto esperado não vazio e escopo com
  um único `project_id` antes de tocar o destino. Depois de concluir todos os
  upserts, o pipeline relê o mesmo escopo e confirma a presença de cada
  `chunk_id` esperado; somente então remove IDs obsoletos daquele `project_id`.
  Uma substituição total dos IDs anteriores permanece permitida quando todos os
  novos IDs estiverem confirmados.
- Identidades de documentos e chunks são determinísticas; `run_id` identifica
  apenas a execução do manifesto. `document_id` recebido no frontmatter (do
  `rag-pipeline`) prevalece sobre a geração determinística local; na ausência
  dele, a geração local é mantida.
- `tenant_id` é opcional no frontmatter. Quando presente em qualquer documento
  do lote de sincronização, a totalidade do lote precisa declará-lo com o
  mesmo valor; o escopo lógico de leitura e remoção em modo espelho passa a
  ser `project_id` + `tenant_id`, isolando a limpeza de obsoletos entre
  tenants que compartilham o mesmo `project_id`. Sem `tenant_id` no lote, o
  escopo continua sendo somente `project_id`, como antes do SPEC-0002.
- `status` presente em `config.yaml` (`contrato_markdown.status_bloqueado`)
  exclui o documento da indexação antes do chunking; a lista é vazia por
  padrão (fail-open) e não fixa valores do contrato ainda não publicado pelo
  `rag-pipeline`.
- `type` e `version` do frontmatter são gravados no payload de cada chunk como
  metadado de auditoria e consulta, sem participar da identidade, do
  chunking ou do bloqueio por status.
- `src/pipeline/` continua sem tenant persistente com autenticação/permissões
  próprias — apenas o isolamento de escopo lógico descrito acima. Desde a
  SPEC-0012, `src/app/` persiste `tenant_id` e `project_id` como dado próprio
  nas tabelas `bases`, `executions` e `queries`, aplicando papéis
  (owner/admin/member) por um token estático de demonstração — ver
  `.specsfy/RULES.md`.
- A tabela `bases` implementa a exclusão lógica e o ownership/retenção
  confirmados em `Informações a guardar confirmadas` abaixo: apagar uma base
  remove `executions`, `queries`, os arquivos no storage e os pontos
  indexados no vector store associado (escopo isolado por base, ver
  `src/app/tasks.py::scope_project_id`), preservando apenas `apagada_em`
  preenchido e `nome` esvaziado como registro mínimo da exclusão.
- O schema de `workspaces`/`bases`/`executions`/`queries` tem migração Alembic versionada
  em `alembic/versions/` desde a reabertura do Ato II da SPEC-0012; `alembic
  upgrade head` usa `APP_DATABASE_URL` (mesma variável do runtime) para
  resolver o destino. Revisões: `074d455d6f67` (schema inicial, SPEC-0012) →
  `f3b60ce4f7f4` (`add documentos to bases`, SPEC-0013) → `4d0fd0aa498e`
  (índice único de execução ativa, SPEC-0015) → `0019_workspaces` (tabela
  `workspaces`, três colunas em `bases`, backfill e índices, SPEC-0019). O
  backfill cria um Workspace padrão por `(tenant_id, project_id)`, associa
  todas as Bases legadas e preserva nelas a coleção global configurada por
  `APP_VECTOR_STORE_COLLECTION` (fallback `rag-pipeline-app`). O downgrade
  remove somente o schema novo e preserva linhas de Base, Execução e Query.
  A suíte de `src/app/` materializa o schema funcional de teste por
  `metadata.create_all` (não altera tabela existente); upgrade, reexecução e
  downgrade da cadeia Alembic são exercitados no banco scratch dedicado de
  `tests/test_app_migrations.py`.
- `bases.documentos` (SPEC-0013) é preenchida na criação com a contagem de
  arquivos recebidos (`src/app/routers/bases.py::enviar_base`,
  `documentos=len(conteudos)`) para upload e base preparada; bases criadas
  antes da migração ficam em `0` (`server_default`) até serem reprocessadas —
  aceitável no ambiente de demonstração. É lida pela listagem
  `GET /api/v1/bases` e pelo detalhe `GET /api/v1/bases/{id}`.

<!-- specsfy:conversation-data:start -->
## Informações a guardar confirmadas

| Informação | Para que serve | O que guardar | Formato sugerido | Ligações | Quem usa | Quando muda ou sai | Fontes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Base de documentos do projeto | Disponibilizar os documentos que serão processados, reprocessados e demonstrados no projeto ativo. | Arquivos Markdown, nome, origem por upload ou base preparada e identificação do projeto ativo. | Arquivos para os documentos e textos curtos para nome e origem. | Pertence ao tenant e ao projeto ativo; origina uma ou mais execuções, chunks e vetores. | Owner e admin podem enviar, administrar e apagar; member pode consultar sem apagar. | Permanece enquanto o projeto existir. Owner ou admin pode apagar quando precisar, mediante confirmação; a exclusão remove conteúdo, execuções, consultas, chunks e vetores associados e preserva somente um registro sem conteúdo de que a exclusão ocorreu. | specs/inbox/2026-08-31-220507-finalizar-ingestao-de-documentos-e-preparar-front-para-apresentacao.md; specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md |
| Execução do pipeline | Acompanhar o processamento, comprovar o resultado e permitir auditoria e reexecução. | Base e origem usadas, situação e etapas, contagens, horários de início e término, erros e manifesto de auditoria. | Escolha entre situações para o estado, números para contagens, datas e horários para acontecimentos, texto para erros e registro de auditoria para o manifesto. | Pertence a uma base, a um tenant e a um projeto; liga documentos, chunks, vetores e consultas de validação. | Owner e admin podem iniciar, repetir, consultar e administrar; member pode acompanhar e consultar, sem apagar. | Permanece com a base enquanto o projeto existir e é removida com seu conteúdo quando owner ou admin apaga a base, preservando somente o registro mínimo da exclusão. | specs/inbox/2026-08-31-220507-finalizar-ingestao-de-documentos-e-preparar-front-para-apresentacao.md; specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md |
| Consulta de validação da recuperação | Demonstrar e auditar o que foi recuperado da base indexada. | Pergunta realizada, resultado recuperado, chunks-fontes apresentados e horário da consulta. | Texto para pergunta e resultado, lista de referências para chunks-fontes e data e horário para a consulta. | Pertence ao tenant, ao projeto, à base consultada e à execução que produziu a indexação. | Owner, admin e member podem realizar e consultar; somente owner e admin administram o histórico por meio da base. | Permanece com a base enquanto o projeto existir e é removida quando owner ou admin apaga a base, preservando somente o registro mínimo da exclusão. | specs/inbox/2026-08-31-220507-finalizar-ingestao-de-documentos-e-preparar-front-para-apresentacao.md; specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md |
| Workspace de organização de bases | Agrupar as bases de um mesmo cliente ou engajamento (ex.: 'Banda Larga PF — Vivo — Gold'), facilitando organização e visualização, e permitindo que bases do mesmo Workspace usem a mesma coleção do banco vetorial ou coleções separadas. | Nome livre curto do Workspace. | Texto curto para o nome. | Toda base passa a pertencer obrigatoriamente a um Workspace; bases existentes hoje são migradas para um Workspace padrão criado na migração. Diferente do project_id/tenant_id técnico já existente, que continua isolando dados entre tenants sem mudança. | Owner e admin podem criar, editar, apagar Workspaces e enviar arquivos; member só visualiza, sem enviar arquivos nem gerenciar o Workspace (mesma regra já aplicada às Bases). | Permanece enquanto tiver bases dentro. Apagar um Workspace com bases dentro é bloqueado; a pessoa precisa apagar ou mover as bases antes. | specs/backlog/0024-agrupar-bases-em-projetos-com-controle-de-colecao-e-metadados.md; specs/inbox/2026-09-17-152835-arrumar-a-qualidade-visual-do-frontend.md |
| Metadados customizados por chunk | Permitir taguear e depois filtrar chunks na busca, dando controle sobre a estratégia de RAG (ex.: separar conteúdo por categoria como 'política' ou 'produto'). | Pares livres de rótulo e valor definidos pela pessoa no momento do upload de uma base (ex.: categoria=política, área=RH). | Lista de pares de texto curto (rótulo e valor), sem lista fixa pré-definida. | Fica ligado a cada chunk gerado a partir dos arquivos enviados numa base; a base pertence a um Workspace. | Quem envia uma base (owner, admin ou member) define os pares no momento do upload. | Permanece com o chunk enquanto ele existir; é removido junto quando a base é apagada, como os demais dados do chunk. | specs/backlog/0024-agrupar-bases-em-projetos-com-controle-de-colecao-e-metadados.md; specs/inbox/2026-09-17-152835-arrumar-a-qualidade-visual-do-frontend.md |
<!-- specsfy:conversation-data:end -->
