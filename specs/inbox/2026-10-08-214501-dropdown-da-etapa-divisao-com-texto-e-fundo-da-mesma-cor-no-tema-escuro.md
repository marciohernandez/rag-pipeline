# Inbox: Dropdown da etapa Divisão com texto e fundo da mesma cor no tema escuro

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-08T21:45:01Z |
| Slug | dropdown-da-etapa-divisao-com-texto-e-fundo-da-mesma-cor-no-tema-escuro |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `c43308f182f636844299246bba6a075e4dcdfbcfa76f57c3a1ee87c059e87885` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

quando abro o dorpdonw não aparece a outra opção porque o fundo do dropdown e a cor da letra são os mesmos

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** No tema escuro, a lista aberta do seletor Estratégia de divisão mostra as opções não selecionadas com texto claro sobre fundo claro, ficando invisíveis.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** A opção Recursivo por caracteres não aparece ao abrir o dropdown; a pessoa não consegue escolher a estratégia pelo mouse.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Owner/admin que cria Bases pelo fluxo de Nova Base no tema escuro.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Opções legíveis em qualquer tema, com contraste adequado.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: fundo e letra com a mesma cor ao abrir o dropdown (print da etapa Divisão, 2026-10-08). Inferência confirmada no código: frontend/src/features/ingestao/EtapaDivisao.tsx:21 e EtapaPublicacao.tsx:27 usam select nativo com bg-transparent; as options herdam texto claro e o navegador no Windows desenha a lista com fundo branco; globals.css define color-scheme dark em .dark.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** Afeta também o seletor de conexões na etapa Publicação; o BACKLOG-0036 vai reescrever a etapa Divisão.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Aplicar bg-popover e text-popover-foreground às options dos selects nativos do fluxo de ingestão, ou trocar pelo Select do shadcn/ui; incluir no BACKLOG-0036 ou corrigir em branch fix/.

## Pontos a revisar no futuro

**A revisar:** Conferir se há outros select nativos com bg-transparent; conferir em Chrome e Firefox no Windows e no Linux; revisão visual nos dois temas.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
