# Interface do projeto

<!-- markdownlint-disable MD013 -->

Este arquivo é a fonte canônica para construir e reaproveitar a interface.
Atualize-o antes e depois de cada tarefa que criar ou mudar uma tela React.
Leia `DESIGNSYSTEM.MD` antes de escolher a composição macro. Este arquivo
registra componentes, blocos e telas locais; as regras globais de SaaS vivem em
`DESIGNSYSTEM.MD`.

## Base observada

- Backend: Python 3.12+ com uv, LangChain, Pytest, FastAPI (`src/app/`) e Qdrant.
- Frontend: **`frontend/`** — projeto Next.js 16 (App Router) autocontido
  (SPEC-0013, DEC-001), React 19, TypeScript, Tailwind CSS v4, shadcn/ui
  (preset `base-nova`, primitives Base UI) e registry ReUI (`@reui`). Testes
  com Vitest + Testing Library (`test:tdd` = `vitest run`).
- Cliente HTTP único: `frontend/src/lib/api-client.ts` (`apiFetch`/`apiJson`,
  injeta `Authorization: Bearer` da sessão, trata 401 limpando a sessão).
  Sessão em `frontend/src/lib/session.ts` (`sessionStorage`, token de
  demonstração).
- Telas entregues: Login (`/login`), Projeto (`/projeto`), Detalhe da execução
  (`/execucoes/[id]`) e listagem de Workspaces (`/workspaces`).

Este `frontend/` não introduz React/Tailwind no restante do repositório
(tooling Python permanece separado, CI própria).

## Design system

| Item | Localização ou valor | Uso no projeto |
| --- | --- | --- |
| Tokens e tema | `frontend/src/app/globals.css` (Tailwind v4, `@theme`), fontes Geist em `frontend/src/app/layout.tsx` | Cores, tipografia, espaçamento, raio e tema |
| Configuração shadcn/ui | `frontend/components.json` (`style: base-nova`, `iconLibrary: lucide`, aliases `@/components`, `@/lib`) | `components.json`, aliases e registry |
| Registry ReUI | `frontend/components.json` → `registries["@reui"] = https://reui.io/r/{style}/{name}.json` | Itens gratuitos `@reui/c-*` |
| PageHeader compartilhado | `DESIGNSYSTEM.MD` | Um componente reutilizável para lista, detalhe, criação e edição |
| Padrão de dashboard | `DESIGNSYSTEM.MD` | `PageHeader`, filtros, `KPI`, visualização principal e investigação detalhada |
| Padrão de linha | `DESIGNSYSTEM.MD` | `DataGrid` em largura total, coluna `ID`, detalhe clicável por linha e ações de editar e apagar |
| Padrão de formulário | `DESIGNSYSTEM.MD` | Seções, coluna de contexto e painel em duas colunas responsivas |
| Padrão de contexto | `DESIGNSYSTEM.MD` | `Breadcrumb` em todas as telas, com equipe, módulo e tela atual |
| Primitives compartilhadas | `frontend/src/components/ui/` (`button`, `input`, `label`, `alert`) | Primitives shadcn/ui (Base UI) |
| Composições de domínio | `frontend/src/features/` (`auth/`, `bases/`, `execucoes/`) | Componentes de domínio por tela |

## Blocos criados e reaproveitáveis

Registre todos os blocos criados no projeto, inclusive os internos de uma
feature. Um bloco é um componente React com responsabilidade própria, como
grade, formulário, filtro, cabeçalho, cartão, diálogo, painel lateral, estado
vazio, upload ou ação em lote.

| Bloco | Tipo | Arquivo | Origem | Finalidade e API pública | Estados e acessibilidade | Consumidores | Reaproveitar ou estender |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Button` | Primitive | `frontend/src/components/ui/button.tsx` | shadcn/ui (Base UI) | Botão com `variant` (default/outline/secondary/ghost/destructive/link) e `size` | Foco visível (`focus-visible:ring`), `disabled` | `LoginForm` e telas seguintes | Reusar; estender por `variant`/`className` |
| `Input` | Primitive | `frontend/src/components/ui/input.tsx` | shadcn/ui (Base UI) | Campo de texto; repassa props nativas; `aria-invalid` estiliza erro | Foco (`focus-visible:ring`), `disabled`, `aria-invalid` | `LoginForm` e formulários seguintes | Reusar; não recriar campo próprio |
| `Label` | Primitive | `frontend/src/components/ui/label.tsx` | shadcn/ui | Rótulo associável por `htmlFor` | `peer-disabled` | `LoginForm` e formulários | Reusar |
| `Alert` / `AlertDescription` | Primitive | `frontend/src/components/ui/alert.tsx` | shadcn/ui | Container `role="alert"` com `variant` (default/destructive) | Anunciado por leitor de tela (`role=alert`) | `LoginForm` (erro genérico); telas seguintes para falhas | Reusar para retorno de erro/estado; não criar aviso próprio |
| `Skeleton` / `Spinner` | Primitive | `frontend/src/components/ui/{skeleton,spinner}.tsx` | shadcn/ui | Placeholder de carregamento / `Loader2Icon` girando (`role=status`) | — | `DataGridBases` (linhas skeleton); botões em telas seguintes | Reusar para todo estado de carregamento |
| `LoginForm` | Domínio | `frontend/src/features/auth/LoginForm.tsx` | Próprio | Formulário de token (`type=password`), ação "Entrar"; sem props. Sucesso → `saveSession` + `router.push("/projeto")`; falha → `clearSession` + erro genérico inline | Foco: campo é o 1º tabável (sem autofocus); erro em `Alert role=alert` com `aria-describedby`; `enviando` desabilita o botão | `frontend/src/app/login/page.tsx` | Estender só para novos modos de autenticação da demo |
| `PageHeader` | Domínio | `frontend/src/components/PageHeader.tsx` | Próprio | Cabeçalho único das telas autenticadas. Props: `title`, `description?`, `status?` (ReactNode ao lado do título), `actions?` (ReactNode à direita) | — | `projeto/page.tsx`; telas de detalhe seguintes | **Reusar sempre**; variar por props, nunca replicar o markup |
| `LayoutAutenticado` | Shell | `frontend/src/app/(autenticado)/layout.tsx` | Próprio | Guarda de sessão (`hasSession()` → senão `router.replace("/login")`), trilha (Equipe → Projeto → tela) e ação "Sair" (`clearSession` + volta ao Login, AC-003) | `pronto` evita divergência de hidratação; renderiza `null` até confirmar sessão no cliente | Todas as rotas em `app/(autenticado)/` | Estender a trilha por props quando surgir a tela de detalhe |
| `DataGridBases` | Domínio | `frontend/src/features/bases/DataGridBases.tsx` | Próprio (tabela semântica) | Listagem de bases. Props: `bases: BaseResumo[]`, `carregando?`, `papel?`, `onBaseApagada?(id)`. Coluna `ID` sempre visível e 1ª; linha inteira é link para `/execucoes/{id}` por mouse e teclado (Enter/Espaço); célula de ações (não propaga o clique) tem "Apagar" para owner/admin → abre `ExcluirBaseDialog` | Carregando com `aria-busy`, texto para leitor e 3 linhas `Skeleton`; vazio (mensagem + convite a enviar); linha `tabIndex=0` com `aria-label="Base {id}"` e `focus-visible:ring` | `projeto/page.tsx`; `workspaces/[id]/page.tsx` | Se o volume crescer, migrar para `@reui/c-data-grid` |
| `Sheet` (+ `SheetContent`/`Header`/`Footer`/`Title`/`Description`/`Trigger`/`Close`) | Primitive | `frontend/src/components/ui/sheet.tsx` | shadcn/ui (Base UI `Dialog`) | Painel lateral controlado por `open`/`onOpenChange`; conteúdo em portal só quando aberto | Backdrop `bg-black/10` + blur; foco preso; `Close` no canto | `UploadBaseSheet`; painéis contextuais seguintes | Reusar; não criar overlay próprio |
| `UploadBaseSheet` | Domínio | `frontend/src/features/bases/UploadBaseSheet.tsx` | Próprio | Envio de base. Props: `open`, `workspaceId?`, `onOpenChange?`, `onCreated(baseId?)`. Input `.md` múltiplo + lista com "Remover"; ação "Enviar" (`FormData` → `POST /api/v1/bases`) e "Usar base preparada" (`URLSearchParams usar_base_preparada=true`). Quando informado, `workspaceId` segue nos dois tipos de envio. Valida limites (50 arquivos, 5 MB/arquivo, 50 MB total, extensão `.md`) **antes** de chamar o backend | Erro em `Alert` `role=alert`; "Enviando…" desabilita as ações; nenhuma base parcial em envio inválido | `projeto/page.tsx`; `workspaces/[id]/page.tsx` associado ao Workspace | Estender com coleção e metadados na T034; trocar o input nativo por `@reui/c-file-upload` se precisar de dropzone |
| `Badge` | Primitive | `frontend/src/components/ui/badge.tsx` | shadcn/ui (Base UI) | Selo com `variant` (default/secondary/destructive/outline/ghost/link) | — | `PainelProgresso` (situação) | Reusar para status e rótulos curtos |
| `PainelProgresso` | Domínio | `frontend/src/features/execucoes/PainelProgresso.tsx` | Próprio | Progresso de uma execução. Props: `execucao: Execucao`, `papel?`, `onRepetida?(id)`. Mostra etapa, `Badge` de situação, contagens previstos/inseridos/mantidos/removidos; "Repetir" só p/ `failed` + owner/admin → `POST /executions/{id}/retry`; aviso `role=status` quando `pending`/`running` | Ativa (aviso, sem ação), falha (erro seguro em `Alert`), "Repetindo…" desabilita | `execucoes/[id]/page.tsx` | Estender com `Timeline` (`@reui/c-timeline`) se a etapa virar lista de passos |
| `Dialog` (+ `DialogContent`/`Header`/`Footer`/`Title`/`Description`/`Close`) | Primitive | `frontend/src/components/ui/dialog.tsx` | shadcn/ui (Base UI `Dialog`) | Modal centrado controlado por `open`/`onOpenChange`; `role="dialog"`; backdrop | Foco preso; `Close` no canto | `ExcluirBaseDialog`; confirmações seguintes | Reusar; não criar modal próprio |
| `ChunksFontes` | Domínio | `frontend/src/features/execucoes/ChunksFontes.tsx` | Próprio | Lista de trechos recuperados. Props: `chunks: ChunkFonte[]` (`{chunk_id, documento, trecho}`). Cada item mostra "Fonte: {documento}" em texto (não só cor, AC-018) + o trecho | Vazio → não renderiza nada | `FormularioConsulta` | Reusar; estender item se o backend trouxer score/posição |
| `FormularioConsulta` | Domínio | `frontend/src/features/execucoes/FormularioConsulta.tsx` | Próprio | Consulta à base. Props: `baseId`. `Label`+`Input` "Pergunta", "Consultar" → `POST /api/v1/bases/{id}/query`; resultado + `ChunksFontes` numa região `role="status"`/`aria-live` (AC-018); falha → `Alert role=alert` com mensagem segura e pergunta preservada (AC-013) | Consultando ("Consultando a base…"), sucesso (resultado + fontes), falha (erro seguro), botão desabilitado sem pergunta | `execucoes/[id]/page.tsx` (quando há execução `succeeded`) | Reusar; a região viva já cobre o anúncio assistivo |
| `ExcluirBaseDialog` | Domínio | `frontend/src/features/bases/ExcluirBaseDialog.tsx` | Próprio | Confirmação de exclusão. Props: `open`, `onOpenChange?`, `base:{id,nome}`, `papel?`, `onDeleted(id)`. Mostra nome + consequência (execuções, consultas, vetores); "Apagar" (`variant=destructive`) só p/ owner/admin → `DELETE /api/v1/bases/{id}` e `onDeleted` | "Apagando…" desabilita; erro em `Alert`; para member a ação nem aparece (AC-019) | `DataGridBases` (ação por linha), `execucoes/[id]/page.tsx` (ação "Apagar base") | Reusar para toda exclusão de base; não duplicar a confirmação |
| `DataGridWorkspaces` | Domínio | `frontend/src/features/workspaces/DataGridWorkspaces.tsx` | Próprio (tabela semântica) | Listagem de Workspaces. Props: `workspaces: WorkspaceResumo[]`, `carregando?`, `podeCriar?`. Coluna `ID` sempre visível; linha inteira abre `/workspaces/{id}` por mouse, Enter ou Espaço | `aria-busy` e 3 linhas `Skeleton` no loading; vazio orienta conforme permissão; linha com nome acessível, foco visível e navegação por teclado | `workspaces/page.tsx` | Reusar na lista; manter ações de editar/apagar no detalhe do Workspace |
| `WorkspaceFormSheet` | Domínio | `frontend/src/features/workspaces/WorkspaceFormSheet.tsx` | Próprio, sobre `Sheet` | Criação/edição de Workspace. Props: `open`, `workspace?`, `onOpenChange?`, `onSaved(workspace)`. Sem `workspace` faz POST; com valor faz PATCH | Nome obrigatório com `aria-invalid`/`aria-describedby`, erro em `Alert`, loading desabilita campo e ações | `workspaces/[id]/page.tsx`; listagem será conectada na T032 | Reusar para criar e editar; não duplicar formulário |
| `ExcluirWorkspaceDialog` | Domínio | `frontend/src/features/workspaces/ExcluirWorkspaceDialog.tsx` | Próprio, sobre `Dialog` | Confirma exclusão. Props: `open`, `workspace`, `temBases`, `papel?`, `onOpenChange?`, `onDeleted(id)`. Executa DELETE apenas para owner/admin e Workspace vazio | Com Bases mostra explicação textual e desabilita apagar; member não recebe ação; erro seguro em `Alert`; loading desabilita controles | `workspaces/[id]/page.tsx` | Reusar para toda exclusão de Workspace |

## Telas e composição

| Tela ou rota | Arquivo | Componentes React usados | Dados e ações | Estados |
| --- | --- | --- | --- | --- |
| Login `/login` | `frontend/src/app/login/page.tsx` | `LoginForm` (que usa `Label`, `Input`, `Alert`, `Button`) | Entrada: token colado. Ação: "Entrar" → `GET /api/v1/bases` valida; sucesso guarda sessão e vai a `/projeto` | Enviando (botão "Entrando…" desabilitado), erro (Alert genérico, campo preservado). Tela isolada: sem `Breadcrumb` nem shell autenticado |
| Projeto `/projeto` | `frontend/src/app/(autenticado)/projeto/page.tsx` (shell `app/(autenticado)/layout.tsx`) | `PageHeader` (ação "Enviar base"), `DataGridBases`, `UploadBaseSheet`, `Alert` (erro de leitura) | `GET /api/v1/bases` na montagem e após envio; linha → `/execucoes/{id}` | Carregando (skeleton), vazio, erro de leitura, sucesso |
| Detalhe `/execucoes/[id]` | `frontend/src/app/(autenticado)/execucoes/[id]/page.tsx` | `PageHeader`, `PainelProgresso`, `FormularioConsulta` (+`ChunksFontes`), `ExcluirBaseDialog`, `Alert`, `Badge`, `buttonVariants`/`next/link` ("Voltar") | `[id]` = id da base; `GET /api/v1/bases/{id}`, polling a cada 3 s enquanto a execução mais recente está `pending`/`running`; "Repetir" (owner/admin, só `failed`) → `POST /executions/{id}/retry`; "Apagar base" (owner/admin) → `DELETE` e volta ao projeto; consulta quando há execução `succeeded` | Carregando, 404 "Base não encontrada", execução atual + histórico, execução ativa, falha com erro seguro, consulta (carregando/sucesso/falha) |
| Workspaces `/workspaces` | `frontend/src/app/(autenticado)/workspaces/page.tsx` | `PageHeader`, `DataGridWorkspaces`, `Alert`, `Button` | `GET /api/v1/workspaces`; owner/admin veem "Criar Workspace" (formulário será conectado na T032); member recebe listagem somente leitura; linha abre o detalhe | Loading com skeleton, vazio contextual à permissão, erro seguro com "Tentar novamente" e sucesso |
| Workspace `/workspaces/[id]` | `frontend/src/app/(autenticado)/workspaces/[id]/page.tsx` | `PageHeader`, `DataGridBases`, `UploadBaseSheet`, `WorkspaceFormSheet`, `ExcluirWorkspaceDialog`, `Alert` | `GET /api/v1/workspaces/{id}` + `GET /api/v1/bases?workspace_id={id}`; linha de Base abre execução; owner/admin podem abrir envio, edição e exclusão; member apenas lê | Loading, 404 específico, erro recuperável, vazio e sucesso; exclusão bloqueada enquanto houver Base |

## Regras de composição

1. Páginas e rotas coordenam dados e compõem componentes; não concentram a
   grade, formulário, filtros, overlays ou cartões reutilizáveis.
2. Antes de criar um componente, consulte esta tabela e reaproveite o item
   existente quando ele atender à mesma intenção.
3. Todo item instalado de shadcn/ui ou ReUI entra na tabela com seu arquivo,
   origem, explicação, API, estados e consumidores reais.
4. ReUI usa somente itens gratuitos `@reui/c-*`; use shadcn/ui para
  primitives e ReUI para composições de produto.
5. Para dashboards, registre a pergunta operacional, escopo, filtros,
   indicadores, visualizações, tabela de investigação e estados. Prefira
   blocos existentes de ReUI e primitives shadcn/ui antes de criar uma nova
   composição.
6. Em CRUD, reutilize o mesmo `PageHeader` nas telas de lista, detalhe,
   criação e edição. Registre uma única implementação, suas props, variações e
   consumidores; não duplique markup de cabeçalho por página.
7. Linhas de `DataGrid` com detalhe usam link acessível em toda a área; a
   listagem ocupa a largura disponível, exibe a coluna `ID` e oferece ações de
   editar e apagar. Ações internas usam `TableRowAction` ou equivalente e não
   propagam a navegação.
8. Formulários de criar e editar usam seções com coluna de contexto e painel
   em duas colunas nos breakpoints largos, refluindo para uma no mobile.
9. Toda tela renderiza `Breadcrumb` com o nome da equipe ativa, o módulo e o
   título atual. Em Laravel, reaproveite o `Breadcrumb` ou `Breadcrumbs` do
   layout existente e registre o componente real em vez de criar outro.
10. Ao criar um bloco, registre-o nesta tabela na mesma tarefa. Ao alterar ou
  remover um bloco, atualize seus consumidores e a orientação de reuso.

<!-- markdownlint-enable MD013 -->
