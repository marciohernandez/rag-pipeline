# Backlog: Agrupar bases em Workspaces com controle de coleção e metadados

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0024 |
| Status | Promoted |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-09-17 |
| Spec promovida | specs/defined/0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados/spec.md |

## Ideia original

eu quero projetos separados onde todos os arquivos que serão feitos o upsert estarem nele, assim facilita a organização e vizualização. Gosto muito de como o Flowsie faz no document store.

## Vocabulário

**Decisão:** a entidade nova desta entrega chama-se **Workspace**, não "Projeto". A palavra "Projeto" já está em uso no sistema com outro sentido — o escopo técnico de isolamento multi-tenant (`Base.project_id`, ver `.specsfy/DATABASE.md`, tabela "Base de documentos do projeto"). Usar o mesmo nome para os dois conceitos causaria homonímia; o usuário confirmou "Workspace" para a nova entidade nesta conversa (aprofundamento via `$specsfy-data-discovery`).

## Problema percebido

Hoje as "bases" existem soltas, sem agrupamento por cliente/engajamento, e o nome de coleção do vector store tem um default global único ('rag_docs' em src/pipeline/indexing.py); não há como organizar múltiplos arquivos/bases sob um mesmo cliente/engajamento nem decidir estratégia de coleções (uma só vs. separadas por tipo de conteúdo).

## Pessoa afetada ou beneficiada

Marcio, organizando bases de conhecimento por cliente/engajamento de consultoria (exemplo dado: 'Banda Larga PF da Vivo, empresa Gold').

## Resultado ou valor esperado

Um Workspace (ex.: por cliente/engajamento) agrupa uma ou mais Bases existentes. Cada Base dentro do Workspace pode apontar para a mesma coleção do banco vetorial ou para uma coleção separada (ex.: uma coleção 'produtos e serviços', outra 'políticas'), dando controle sobre a estratégia de RAG. Também é possível configurar metadados customizados por chunk no momento do upload, para taguear e filtrar depois.

## Contexto

Depende do item 0023 (nome de coleção configurável), que passa a ser aplicado por Base dentro de um Workspace, em vez de um default global único. Existe um `project_id` técnico já no banco (`Base.project_id`, `models.py`) usado para isolamento multi-tenant via token de autenticação (`main.py`) — o usuário confirmou que o Workspace desta entrega é uma entidade nova e diferente, acima das Bases atuais, sem mudar o `project_id` técnico.

## Referências relacionadas

- `specs/inbox/2026-09-17-152835-arrumar-a-qualidade-visual-do-frontend.md` (origem: captura original, mesma conversa que originou este item).
- `specs/backlog/0023-expor-configuracoes-de-ingestao-na-interface.md` (backlog relacionado: nome de coleção configurável, base deste item).
- `src/app/models.py`, `src/app/tasks.py`, `src/app/main.py` (documentação relacionada: `project_id`/`tenant_id` técnicos já existentes, usados para isolamento multi-tenant, distintos do Workspace desta entrega).
- `.specsfy/DATABASE.md` (seção "Informações a guardar confirmadas": "Workspace de organização de bases" e "Metadados customizados por chunk", registrados nesta conversa via `$specsfy-data-discovery`).

## Comportamento esperado

- **Decisão:** toda Base passa a pertencer obrigatoriamente a um Workspace. As Bases já existentes hoje (sem Workspace) são migradas automaticamente para um Workspace padrão criado na migração. Não existe mais o estado "Base sem Workspace".
- **Decisão:** dentro de um Workspace, cada Base pode apontar para a mesma coleção do banco vetorial que outra Base do mesmo Workspace, ou para uma coleção diferente — a pessoa escolhe por Base, reaproveitando o campo de nome de coleção do item 0023.
- **Decisão:** é possível configurar metadados customizados por chunk no momento do upload de uma Base, como pares livres de rótulo e valor (ex.: categoria=política, área=RH), definidos pela pessoa a cada upload, sem lista fixa pré-definida.
- **Decisão:** o Workspace guarda apenas um nome livre curto (ex.: "Banda Larga PF — Vivo — Gold"); não há campos separados de cliente/empresa nem descrição longa.

## Regras de negócio

- **Decisão (autorização):** `owner` e `admin` podem criar, editar, apagar Workspaces e fazer upload de arquivos; `member` só visualiza Workspaces e Bases, sem enviar arquivos nem gerenciar o Workspace. Corrigido nesta conversa para manter a regra já implementada em Bases (`require_write_role`, SPEC-0013) — a resposta inicial ("member também envia") continha um conflito com o código atual, resolvido a favor de preservar o comportamento existente.
- **Decisão (exclusão):** apagar um Workspace que ainda contém Bases é bloqueado. A pessoa precisa apagar ou mover todas as Bases do Workspace antes de poder apagá-lo.
- A esclarecer: um Workspace pode ficar sem nenhuma Base (vazio) permanentemente, ou é apagado automaticamente quando fica vazio?

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado; depende do detalhamento de telas (Contrato de experiência de interface).

## Qualidades e operação

- Segurança: isolamento entre tenants continua garantido pelo `project_id`/`tenant_id` técnicos existentes; a autorização por papel (owner/admin/member) dentro de um Workspace é regra nova desta entrega.
- Privacidade: a avaliar.
- Desempenho e volume: a esclarecer — quantos Workspaces por tenant, quantas Bases por Workspace (sem limite conhecido até o momento).
- Auditoria e observabilidade: a avaliar; recomenda-se seguir o padrão do projeto (registrar criação, edição e tentativa de exclusão bloqueada).

## Dependências

- Item 0023 (nome de coleção configurável por Base) — pré-requisito funcional para a escolha de coleção por Base dentro de um Workspace.
- Migração de dados das Bases existentes para um Workspace padrão, antes ou junto da entrega desta funcionalidade.

## Situações de erro

- Tentativa de apagar Workspace com Bases dentro → bloqueado, com mensagem explicando a consequência (decisão já registrada acima).
- A esclarecer: erro ao tentar mover uma Base entre Workspaces (se essa ação existir).

## Escopo

- Dentro: nova entidade Workspace; migração das Bases existentes para Workspace padrão; escolha de coleção por Base dentro do Workspace; metadados customizados por chunk no upload; autorização por papel para gerenciar Workspaces.
- Fora: mudança no `project_id`/`tenant_id` técnico de isolamento multi-tenant; mover Base entre Workspaces (a esclarecer se entra).

## Dúvidas, decisões e riscos

- **Resolvida:** nome da entidade — "Workspace" (ver Vocabulário).
- **Aberto:** um Workspace vazio (sem Bases) é permitido permanentemente ou apagado automaticamente?
- **Aberto:** existe ação de mover uma Base entre Workspaces?
- **Risco:** mudança estrutural em modelo de dados (nova entidade acima de `Base`, migração de dados existentes) — maior risco que os itens 0022 e 0023.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente (falta Gherkin/critérios de aceite, a produzir na especificação).
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco (privacidade e volume ainda a esclarecer).
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa (dúvidas em aberto sobre Workspace vazio e mover Base) ou avançar para `$specsfy-03-specify` com as decisões já tomadas.
