# Inbox: Documentator varre frontend/.next e acusa docs desatualizado

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-09-17T19:00:09Z |
| Slug | documentator-varre-frontend-next-e-acusa-docs-desatualizado |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `66fd2a8430ecea3ebd30126f3d67c9316ed0469106ccf502de786a8c57a0711d` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

build_documentation.mjs acusa docs/ desatualizado por causa do cache frontend/.next/

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** A lista fixa de ignorados do build_documentation.mjs não inclui .next, então o cache de build do Next.js entra na varredura e faz o --check acusar documentação desatualizada sem drift real.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Com um dev server Next rodando (ou qualquer build recente), frontend/.next existe e é varrido: a contagem de 'arquivos de código' salta de 271 para 361 e docs/frontend.md passa a listar CSS gerado em .next/dev/static/chunks/. O --check então reprova docs/README.md, architecture.md, application.md e frontend.md. Removendo o cache, o --check passa e docs/ fica idêntico ao commitado — ou seja, o drift não existia.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Qualquer pessoa ou agente que rode o documentator neste projeto depois de um npm run dev ou npm run build; o efeito é pedir commit de artefato efêmero em docs/.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Não identificado no texto original.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Lista de ignorados observada em .agents/skills/specsfy-documentator/scripts/build_documentation.mjs: .git, .venv, build, coverage, dist, docs, node_modules, storage, vendor — sem .next. O diretório está no frontend/.gitignore (/.next/), então git o ignora mas o documentator não. Observado durante T044 da SPEC-0013 em 2026-09-17.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** O script é instalado pelo CLI specsfy em .agents/skills/, então editar localmente seria sobrescrito num specsfy update — a correção provavelmente pertence ao repositório do framework, não a este projeto. Enquanto isso, o contorno é apagar frontend/.next antes de rodar o documentator, o que é fácil de esquecer e já causou uma reconstrução poluída nesta sessão.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Acrescentar .next à lista de ignorados do documentator, ou fazer o script respeitar os .gitignore aninhados do projeto em vez de uma lista fixa.

## Pontos a revisar no futuro

**A revisar:** Falta decidir se isso vira um item local (contorno documentado em RULES.md) ou um reporte para o repositório do framework specsfy. Também não foi verificado se outros artefatos comuns ficam de fora da lista, como .turbo, .svelte-kit ou target.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
