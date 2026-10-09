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
| Banco vetorial principal | Collection Qdrant remota | `config.yaml`, `src/pipeline/providers/vectorstores/qdrant.py` |
| Backend de aplicação | PostgreSQL | `APP_DATABASE_URL`, `src/app/db.py`, `src/app/models.py`, `alembic/versions/0020_pessoas_e_autoria.py` |
| Arquivos enviados | Cloudflare R2 ou disco local de desenvolvimento | `src/app/storage.py` |

## Estruturas detectadas

| Estrutura | Tipo | Campos | Relações | Fonte |
| --- | --- | --- | --- | --- |
| Documento Markdown | Arquivo | Conteúdo, frontmatter, identidade e hash de origem | Origina documento e chunks | `src/pipeline/loader.py`, `src/pipeline/identity.py` |
| Chunk auditável | JSON e ponto vetorial | Conteúdo, `chunk_id`, `document_id`, `project_id`, `tenant_id` e metadados | Pertence a um documento | `src/pipeline/exporter.py`, `src/pipeline/providers/vectorstores/qdrant.py` |
| `workspaces` | Tabela PostgreSQL | `id`, `tenant_id`, `project_id`, `nome`, `criado_por` opcional, `criado_em`, `apagada_em`; índices de escopo e autoria | Tem várias Bases; `criado_por` referencia Pessoa; exclusão lógica | `src/app/models.py`, revisões `0019_workspaces` e `0020_pessoas` |
| `bases` | Tabela PostgreSQL | `id`, `tenant_id`, `project_id`, `workspace_id`, `nome`, `origem`, `collection_name`, `metadados_chunk`, `documentos`, `conexao_embeddings_id` e `conexao_vector_store_id` (FKs opcionais para `conexoes`, `ON DELETE RESTRICT`), `chunking` (JSON opcional com `splitter`, `chunk_size` e `chunk_overlap` e, desde a SPEC-0029, as chaves opcionais `opcoes` (`nivel_cabecalho`, `separador`, `encoding`, `remover_cabecalhos`), `resumos` (`ativo`, `minimo_subsecoes`), `qualidade` (`minimo_util`), `contrato` (`status_bloqueado`) e `destino` (`batch_size`, `sync_mode`); chaves ausentes usam os padrões de `src/app/ingestao.py`, sem migration), `criado_por` opcional, `criado_em`, `apagada_em` | Pertence a Workspace e Pessoa; referencia até duas Conexões (nulas nas Bases anteriores à SPEC-0026); tem Execuções e Consultas | `src/app/models.py`, revisões até `0020_pessoas` |
| `executions` | Tabela PostgreSQL | `id`, `base_id`, `situacao`, `etapa`, contagens, `erro`, datas e `criado_por` opcional; índice único parcial de execução ativa | Pertence a Base e Pessoa | `src/app/models.py`, revisões `4d0fd0aa498e` e `0020_pessoas` |
| `queries` | Tabela PostgreSQL | `id`, `base_id`, `tenant_id`, `project_id`, `pergunta`, `resultado`, `chunks_fontes`, `criado_por` opcional e `criado_em` | Pertence a Base e Pessoa | `src/app/models.py`, revisão `0020_pessoas` |
| `pessoas` | Tabela PostgreSQL | `id`, `nome`, `email`, `senha_hash`, `precisa_trocar_senha`, `situacao`, `criada_por` opcional, `criada_em`, `atualizada_em`; índice único em `lower(email)` | Tem um Vínculo e Sessões; pode criar Pessoas e demais registros; nunca é apagada | `src/app/models.py`, revisão `0020_pessoas` |
| `vinculos_pessoa` | Tabela PostgreSQL | `id`, `pessoa_id` único, `tenant_id`, `project_id`, `papel`; índice de escopo | Liga uma Pessoa a exatamente um tenant/projeto e papel nesta entrega | `src/app/models.py`, revisão `0020_pessoas` |
| `sessoes` | Tabela PostgreSQL | `id`, `pessoa_id`, `token_hash` único, `criada_em`, `expira_em`; índices de pessoa, token e expiração | Pertence a Pessoa; apagada ao encerrar ou expirar | `src/app/models.py`, revisão `0020_pessoas` |
| `tentativas_login` | Tabela PostgreSQL | `email_normalizado`, `falhas_seguidas`, `bloqueada_ate`, `atualizada_em` | Sem FK para não revelar a existência de conta | `src/app/models.py`, revisão `0020_pessoas` |
| `eventos_acesso` | Tabela PostgreSQL | `id`, `tipo`, `motivo`, `ator_pessoa_id`, `alvo_pessoa_id`, `tenant_id`, `project_id`, `criado_em` | Ator e alvo opcionais referenciam Pessoas; retenção de 90 dias | `src/app/models.py`, `src/app/events.py`, revisão `0020_pessoas` |
| `conversas_assistente` | Tabela PostgreSQL | `id`, `tenant_id`, `project_id`, `pessoa_id` (FK `pessoas.id`), `titulo` (até 60 caracteres; "Nova conversa" até a primeira mensagem), `criada_em`, `atualizada_em`; índice (`pessoa_id`, `atualizada_em`) | Pertence a uma Pessoa; visível só à autora; tem muitas mensagens | `src/app/models.py` (`ConversaAssistente`), `src/app/repo.py`, revisão `0021_assistente` (SPEC-0021) |
| `mensagens_assistente` | Tabela PostgreSQL | `id`, `conversa_id` (FK `conversas_assistente.id`, `ON DELETE CASCADE`), `papel` (`pessoa` ou `assistente`), `conteudo`, `base_id` (sem chave estrangeira; sobrevive à exclusão lógica da Base), `fontes` (JSON com os arquivos citados), `criada_em`; índice (`conversa_id`, `criada_em`) | Pertence a uma conversa; imutável; removida com ela | `src/app/models.py` (`MensagemAssistente`), `src/app/repo.py`, revisão `0021_assistente` (SPEC-0021) |
| `conexoes` | Tabela PostgreSQL | `id`, `tenant_id`, `project_id`, `nome` (até 80 caracteres), `tipo` (`embeddings_openai` ou `qdrant`), `situacao` (`ativa` ou `desativada`), `configuracao` (JSON não secreto), `segredo_cifrado` (texto Fernet, nunca em claro), `criado_por` opcional, `criado_em`, `atualizada_em`; índices de autoria e de escopo com situação | Pertence a tenant e projeto; criada por Pessoa; referenciada por zero ou mais Bases | `src/app/models.py` (`Conexao`), revisão `0026_conexoes_ingestao` (SPEC-0026) |
| `eventos_conexao` | Tabela PostgreSQL | `id`, `tenant_id`, `project_id`, `conexao_id` (sem FK; sobrevive à exclusão), `acao` (criada, editada, chave_trocada, desativada, reativada, excluida), `ator_pessoa_id` opcional, `criado_em`; nunca guarda valores de campos | Referencia a Pessoa autora; retenção de 90 dias | `src/app/models.py` (`EventoConexao`), revisão `0026_conexoes_ingestao` (SPEC-0026) |
<!-- specsfy:database:end -->

Nota: ChromaDB e Pinecone foram removidos como providers concretos de vector
store pela SPEC-0010 (2026-09-04); Qdrant é hoje o único backend real, com a
abstração multi-provider mantida aberta em `src/pipeline/providers/` para
novos destinos futuros.

## Decisões, ownership e retenção

- Conversas do assistente (SPEC-0021): permanecem até a autora apagar; desativar a pessoa não as apaga, mas ela deixa de acessá-las. Somente a autora lê ou apaga (owner e admin também recebem 404). O conteúdo das mensagens, os trechos da documentação e os trechos da Base apontada saem para o provedor de LLM configurado (OpenRouter), o mesmo padrão já aceito no `chat.py`. Nenhum log registra o conteúdo.
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
  próprias — apenas o isolamento de escopo lógico descrito acima. Em
  `src/app/`, a SPEC-0020 resolve `tenant_id`, `project_id` e papel pelo
  vínculo da Pessoa autenticada em uma Sessão persistida; tokens estáticos
  foram removidos e são recusados.
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
  remove somente o schema novo e preserva linhas de Base, Execução e Query →
  `0020_pessoas` (Pessoas, vínculos, sessões, tentativas, eventos e autoria
  opcional nas quatro entidades existentes). O downgrade de `0020_pessoas`
  remove apenas essas estruturas e colunas → `0021_assistente` (conversas e
  mensagens do assistente) → `0026_conexoes_ingestao` (tabelas `conexoes` e
  `eventos_conexao` e três colunas anuláveis em `bases`, SPEC-0026; o downgrade
  remove somente esse schema novo e preserva linhas de Base, Execução e Consulta).
  A suíte de `src/app/` materializa o schema funcional de teste por
  `metadata.create_all` (não altera tabela existente); upgrade, reexecução e
  inspeção AST do contrato de downgrade são exercitados em schemas exclusivos
  do banco explícito em `.env.testing` por `tests/test_app_migrations.py`.
  Nenhum downgrade ou remoção de tabela é executado pela suíte. Os testes
  comuns usam rollback transacional; casos concorrentes e worker preservam
  seu schema isolado para diagnóstico (T017, SPEC-0022).
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
| Workspace de organização de bases | Agrupar as bases de um mesmo cliente ou engajamento (ex.: 'Banda Larga PF — Vivo — Gold'), facilitando organização e visualização, e permitindo que bases do mesmo Workspace usem a mesma coleção do banco vetorial ou coleções separadas. | Nome livre curto do Workspace. | Texto curto para o nome. | Toda base passa a pertencer obrigatoriamente a um Workspace; bases existentes hoje são migradas para um Workspace padrão criado na migração. Diferente do project_id/tenant_id técnico já existente, que continua isolando dados entre tenants sem mudança. | Owner e admin podem criar, editar, apagar Workspaces e enviar arquivos; member só visualiza, sem enviar arquivos nem gerenciar o Workspace (mesma regra já aplicada às Bases). | Permanece enquanto tiver bases dentro. Apagar um Workspace com bases dentro é bloqueado; a pessoa precisa apagar ou mover as bases antes. | specs/backlog/0026-agrupar-bases-em-projetos-com-controle-de-colecao-e-metadados.md; specs/inbox/2026-09-17-152835-arrumar-a-qualidade-visual-do-frontend.md |
| Metadados customizados por chunk | Permitir taguear e depois filtrar chunks na busca, dando controle sobre a estratégia de RAG (ex.: separar conteúdo por categoria como 'política' ou 'produto'). | Pares livres de rótulo e valor definidos pela pessoa no momento do upload de uma base (ex.: categoria=política, área=RH). | Lista de pares de texto curto (rótulo e valor), sem lista fixa pré-definida. | Fica ligado a cada chunk gerado a partir dos arquivos enviados numa base; a base pertence a um Workspace. | Quem envia uma base (owner, admin ou member) define os pares no momento do upload. | Permanece com o chunk enquanto ele existir; é removido junto quando a base é apagada, como os demais dados do chunk. | specs/backlog/0026-agrupar-bases-em-projetos-com-controle-de-colecao-e-metadados.md; specs/inbox/2026-09-17-152835-arrumar-a-qualidade-visual-do-frontend.md |
| Pessoa com acesso ao sistema | Distinguir cada pessoa da equipe, mesmo com o mesmo papel, para entrar no sistema, ter permissões próprias e ser reconhecida como autora do que faz. | Nome; e-mail (único no sistema); papel (owner, admin ou member); situação (ativa ou desativada); se ainda precisa trocar a senha; a senha, guardada só de forma que ninguém consegue ler; quando foi criada e por quem. | Texto curto para nome e e-mail; escolha entre opções para papel e situação; sim ou não para a troca de senha pendente; data e horário para a criação; a senha nunca é visível nem aparece em resposta, log ou tela. | Pertence a exatamente um tenant e projeto, por um vínculo próprio separado do cadastro; origina sessões, tentativas de entrada, eventos do histórico de acessos e a autoria de Workspaces, Bases, Execuções e Consultas. | Owner e admin criam, listam, corrigem nome e e-mail, alteram o papel, desativam, reativam e redefinem a senha das pessoas do próprio tenant e projeto; admin não altera owner; member não vê a tela de Pessoas; toda pessoa troca a própria senha. | Nunca é apagada, só desativada, para preservar a autoria; pessoa desativada não entra e perde a sessão na hora; o último owner de um tenant não pode ser desativado nem rebaixado; corrigir nome ou e-mail mantém a mesma pessoa e o histórico de autoria. | specs/backlog/0023-autenticacao-real-por-pessoa.md; specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md |
| Vínculo da pessoa com tenant, projeto e papel | Dizer a qual tenant e projeto a pessoa pertence e com qual papel, mantendo o isolamento e as permissões atuais e deixando aberta a evolução futura para mais de um vínculo. | Pessoa, tenant, projeto e papel. | Registro próprio, separado do cadastro da pessoa, com texto curto para tenant e projeto e escolha entre opções para o papel. | Liga uma pessoa a exatamente um tenant e projeto nesta entrega; alimenta a identidade usada por todas as requisições. | Owner e admin do tenant alteram o papel; ninguém muda o tenant ou o projeto de uma pessoa; admin não altera o vínculo de owner. | Existe enquanto a pessoa existir; a mudança de papel encerra a sessão da pessoa na hora. | specs/backlog/0023-autenticacao-real-por-pessoa.md |
| Sessão de acesso da pessoa | Manter a pessoa conectada por um tempo limitado e poder encerrar o acesso na hora quando algo muda na conta. | Pessoa; quando a sessão começou e até quando vale (8 horas fixas). O motivo e o horário do término ficam registrados no histórico de acessos, não na própria sessão, que é apagada ao terminar. | Data e horário para início e validade; o motivo do término (sair, expirar, desativação, mudança de papel, correção de dados ou redefinição de senha) é uma escolha entre opções gravada no histórico de acessos. | Pertence a uma pessoa; cada requisição autenticada depende de uma sessão válida. | Só o próprio sistema consulta e encerra; nenhuma tela lista sessões nesta entrega. | Vale 8 horas sem renovação e termina na hora ao sair, desativar, alterar papel, corrigir nome ou e-mail ou redefinir a senha; é apagada assim que deixa de valer, e só o histórico de acessos permanece pelos 90 dias. | specs/backlog/0023-autenticacao-real-por-pessoa.md |
| Tentativas de entrada e bloqueio da conta | Frear tentativas repetidas de adivinhar uma senha bloqueando a conta por um tempo. | Pessoa ou e-mail tentado; número de erros seguidos; até quando a conta está bloqueada. | Número para os erros seguidos e data e horário para o fim do bloqueio. | Refere-se a uma pessoa; cada bloqueio e cada falha também geram um evento no histórico de acessos. | Só o sistema consulta e altera; a pessoa bloqueada vê apenas o aviso de bloqueio temporário, sem o tempo exato. | 5 erros seguidos bloqueiam a conta por 15 minutos; o contador zera ao entrar com sucesso ou ao fim do bloqueio; é apagado quando deixa de valer. | specs/backlog/0023-autenticacao-real-por-pessoa.md |
| Histórico de acessos e mudanças de conta | Responder depois do fato quem entrou, quem errou a senha, quem foi bloqueado e quem mudou uma conta. | O acontecimento (entrou, errou a senha, foi bloqueada, trocou a senha, teve a senha redefinida, foi criada, teve nome ou e-mail corrigido, teve o papel alterado, foi desativada, foi reativada); quem fez; com quem; quando. Nunca a senha, o hash ou qualquer segredo. | Escolha entre os acontecimentos, referência às pessoas envolvidas e data e horário. | Refere-se à pessoa que agiu e à pessoa afetada, dentro do mesmo tenant e projeto. | Nesta entrega o sistema só registra os acontecimentos; não há tela nem consulta por pessoa (suposição a confirmar na especificação); member não consulta. | Guardado por 90 dias e depois apagado; não altera nem depende da autoria dos demais registros. | specs/backlog/0023-autenticacao-real-por-pessoa.md |
| Autoria dos registros do produto | Mostrar quem criou cada Workspace, Base, Execução e Consulta, para distinguir duas pessoas com o mesmo papel e dar base a auditoria e memória por pessoa. | Referência à pessoa que criou o registro; em registros anteriores à entrega, ausente, exibido como autor não identificado. | Referência à pessoa, opcional, em Workspace, Base, Execução e Consulta. | Cada Workspace, Base, Execução e Consulta aponta para a pessoa que a criou; a pessoa continua ligada aos registros mesmo desativada. | Visível a todos os papéis do tenant e projeto, inclusive member, nas listas e no detalhe. | Acompanha o registro que descreve; permanece com o nome da pessoa mesmo depois de ela ser desativada; não segue o prazo de 90 dias do histórico de acessos. | specs/backlog/0023-autenticacao-real-por-pessoa.md |
| Conexões reutilizáveis para ingestão | Cadastrar conexões pela interface e selecioná-las na etapa de publicação. | Nome, tipo (embeddings OpenAI ou Qdrant), configuração não secreta (modelo, URL base opcional e dimensões; ou URL do Qdrant), chave somente escrita cifrada, situação, autoria e datas; histórico de alterações sem valores. | Texto curto para nome, escolha entre opções para tipo e situação, JSON para a configuração, texto cifrado para a chave. | Compartilhadas dentro da mesma equipe e projeto, reutilizáveis em qualquer Workspace; cada Base publicada guarda a conexão de embeddings e a do Qdrant usadas. | Owner e admin cadastram, editam, desativam, reativam, excluem e usam; member não vê nem usa; a chave nunca é devolvida. | Desativar preserva vínculos, histórico e vetores; novo upsert exige conexão ativa; exclusão definitiva somente sem Base vinculada; o histórico de alterações é purgado após 90 dias. | specs/in-progress/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md; specs/backlog/0025-expor-configuracoes-de-ingestao-na-interface.md |
<!-- specsfy:conversation-data:end -->
