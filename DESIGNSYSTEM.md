# Design system do produto

Este documento governa a composição macro das telas. `INTERFACE.md` registra
os componentes e consumidores concretos.

## Classificação

| Campo | Valor |
| --- | --- |
| Escopo | Produto inteiro |
| Status | Ativo |
| Versão | 1.0.0 |
| Atualizado em | 2026-09-21 |
| Responsável | Projeto rag-pipeline |

## Política de direção

- Na ausência de direção visual específica, aplicar os defaults SaaS abaixo.
- Preservar tokens de `frontend/src/app/globals.css` e primitives locais antes
  de criar variantes.
- Registrar exceções locais com alcance explícito em `INTERFACE.md`.

## Linguagem visual e shell

- Interface operacional e compacta, com hierarquia por tipografia, contraste
  e espaçamento.
- Telas autenticadas usam shell persistente, navegação principal, identidade
  da pessoa e Breadcrumb com Equipe, módulo e tela atual.
- Login e Nova senha são superfícies isoladas, sem navegação do produto.
- Cada tela de produto começa com o `PageHeader` compartilhado.

## CRUD canônico

| Superfície | Composição |
| --- | --- |
| Lista | `PageHeader` + resumo + `DataGrid` em largura total, com ID e ações por linha |
| Detalhe | `PageHeader` + `DetailLists`, situação e ações disponíveis |
| Criar/editar | Seções responsivas; em formulários curtos consolidados, `Sheet` lateral |
| Confirmação | `Dialog` com alvo, consequência, ação secundária e ação semântica |

Linhas de tabela abrem o detalhe por mouse, Enter ou Espaço. Controles internos
não propagam a navegação. Pessoas nunca oferecem apagar: somente desativar ou
reativar, preservando autoria.

## Formulários e estados

- Labels visíveis, autocomplete adequado e ajuda próxima ao campo.
- Erro em vermelho abaixo do campo, `aria-invalid`, foco no primeiro erro e
  valores preservados.
- Cobrir loading, vazio, erro, sucesso, sem permissão, disabled e conteúdo
  longo quando aplicáveis.
- Diálogos e painéis prendem foco, fecham por Escape e devolvem foco ao
  gatilho; ações em envio ficam desabilitadas.
- Mobile usa uma coluna, overlays ocupam a largura útil e tabelas densas rolam
  horizontalmente sem ocultar ID.

## Cenários canônicos

- Lista com registros: cabeçalho, contexto, tabela comparável e ações por linha.
- Lista vazia: motivo, orientação e ação inicial quando permitida.
- Detalhe: situação, atributos agrupados e próxima ação.
- Criação/edição válida: feedback concreto e retorno ao contexto.
- Erro de campo: mensagem associada, foco e dados preservados.
- Sem permissão: explicação curta, nenhum dado protegido e retorno seguro.
- Erro de carregamento: mensagem segura e opção de tentar novamente.

## Exceções ativas

| Data | Fluxo | Exceção | Alcance | Motivo |
| --- | --- | --- | --- | --- |
| 2026-09-21 | Pessoas | Criar e editar usam `Sheet` em vez de página em duas colunas | CRUD de Pessoas | Formulário curto e coerência com Workspaces |
| 2026-09-21 | Pessoas | A linha não oferece apagar | CRUD de Pessoas | Pessoa é desativada para preservar autoria |

## Revisão visual

Conferir em 360 px e desktop: bordas, margens, padding, tipografia, quebra de
e-mail/nome longo, overflow da tabela, foco visível e estados adversos.

## Histórico

| Versão | Data | Alteração |
| --- | --- | --- |
| 1.0.0 | 2026-09-21 | Defaults SaaS e padrões de autenticação, Pessoas e autoria |
