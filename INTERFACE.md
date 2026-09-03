# Interface do projeto

<!-- markdownlint-disable MD013 -->

Este arquivo é a fonte canônica para construir e reaproveitar a interface.
Atualize-o antes e depois de cada tarefa que criar ou mudar uma tela React.
Leia `DESIGNSYSTEM.MD` antes de escolher a composição macro. Este arquivo
registra componentes, blocos e telas locais; as regras globais de SaaS vivem em
`DESIGNSYSTEM.MD`.

## Base observada

- Stack: Python 3.12+ com uv, LangChain, Pytest e bancos vetoriais.
- Interface atual: **nenhuma interface para pessoas**. Este componente é
  operado por linha de comando (`pipeline.py`, `search.py`, `chat.py`).
- Evidência: `inspect_interface.mjs` não encontrou framework, roteamento,
  estilos, componentes, formulários nem testes de interface neste repositório.
- Política registrada abaixo: aplica-se somente se e quando uma interface React
  for criada aqui. Hoje ela não descreve o sistema existente.

O projeto-mãe `rag-pipeline` prevê Next.js, shadcn/ui e Tailwind como direção
futura de integração. Isso não é dependência atual deste componente e não
autoriza introduzir React, Tailwind ou qualquer biblioteca de interface no
`rag-pipeline` sem uma spec que a justifique.

As tabelas seguintes permanecem vazias por serem inaplicáveis ao estado atual.
Preencha-as somente quando uma tela real existir.

## Design system

| Item | Localização ou valor | Uso no projeto |
| --- | --- | --- |
| Tokens e tema | A mapear | Cores, tipografia, espaçamento, raio e tema |
| Configuração shadcn/ui | A mapear | `components.json`, aliases e registry |
| Registry ReUI | A mapear | Itens gratuitos `@reui/c-*` |
| PageHeader compartilhado | `DESIGNSYSTEM.MD` | Um componente reutilizável para lista, detalhe, criação e edição |
| Padrão de dashboard | `DESIGNSYSTEM.MD` | `PageHeader`, filtros, `KPI`, visualização principal e investigação detalhada |
| Padrão de linha | `DESIGNSYSTEM.MD` | `DataGrid` em largura total, coluna `ID`, detalhe clicável por linha e ações de editar e apagar |
| Padrão de formulário | `DESIGNSYSTEM.MD` | Seções, coluna de contexto e painel em duas colunas responsivas |
| Padrão de contexto | `DESIGNSYSTEM.MD` | `Breadcrumb` em todas as telas, com equipe, módulo e tela atual |
| Primitives compartilhadas | A mapear | Componentes em `ui/` ou diretório equivalente |
| Composições de domínio | A mapear | Componentes em `features/` ou diretório equivalente |

## Blocos criados e reaproveitáveis

Registre todos os blocos criados no projeto, inclusive os internos de uma
feature. Um bloco é um componente React com responsabilidade própria, como
grade, formulário, filtro, cabeçalho, cartão, diálogo, painel lateral, estado
vazio, upload ou ação em lote.

| Bloco | Tipo | Arquivo | Origem | Finalidade e API pública | Estados e acessibilidade | Consumidores | Reaproveitar ou estender |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A mapear | Primitive, composição ou domínio | A mapear | shadcn/ui, ReUI ou próprio | Props, eventos e dados esperados | Foco, teclado, loading, vazio, erro e sucesso | Telas e outros blocos | Quando usar; qual bloco estender antes de criar outro |

## Telas e composição

| Tela ou rota | Arquivo | Componentes React usados | Dados e ações | Estados |
| --- | --- | --- | --- | --- |
| A mapear | A mapear | A mapear | A mapear | Carregando, vazio, erro e sucesso |

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
