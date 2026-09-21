# Inbox: review_findings.mjs calcula a raiz errada no layout com pasta de estado

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-09-17T21:19:59Z |
| Slug | review-findings-mjs-calcula-a-raiz-errada-no-layout-com-pasta-de-estado |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Validação da SPEC-0019 (Workspaces) nesta conversa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `cedc501db9f12589a2eb017db6760ee60f1dd6910c55d6d7da9734e09d7572fa` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

review_findings.mjs acusa "evidence local inexistente ou insegura" para arquivos que existem, a menos que se passe --root . explicitamente

## Contexto consultado

.agents/skills/specsfy-04-validate/scripts/review_findings.mjs; specs/draft/0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados/spec.md

## Resumo processado

**Inferência:** O script deriva a raiz do projeto como dirname(spec)/../.., o que assumia o layout antigo specs/<NNNN>-<slug>/spec.md. No layout atual, specs/<estado>/<NNNN>-<slug>/spec.md, esse cálculo aponta para specs/ em vez da raiz, e toda evidência relativa à raiz do projeto é rejeitada.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** A validação de findings falha com erro enganoso (evidence inexistente/insegura) para caminhos válidos, escondendo o resultado real do gate. Só não falha se quem executa souber passar --root . manualmente.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Quem roda a validação de findings em qualquer spec deste projeto, e qualquer projeto consumidor do Specsfy que já use o layout com pasta de estado.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Não identificado no texto original; a correção esperada seria o script resolver a raiz de forma compatível com os dois layouts, ou o contrato passar a exigir --root.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Observado em .agents/skills/specsfy-04-validate/scripts/review_findings.mjs, linha com: const root = args.root ? resolve(args.root) : resolve(dirname(spec), '../..'). O layout canônico documentado em .specsfy/Spec.md é specs/<estado>/<NNNN>-<slug>/, com três níveis.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Nenhuma informação a guardar identificada.

### Riscos e dependências

**Análise preliminar:** O código pertence a .agents/skills/, instalado via npx skills add a partir de promovaweb/specsfy: corrigir localmente pode ser sobrescrito na próxima instalação. Pode caber upstream, não neste repositório.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Hipótese, não requisito: reportar upstream no repositório do Specsfy; ou padronizar a chamada com --root . nas skills que invocam o script.

## Pontos a revisar no futuro

**A revisar:** Confirmar se outros scripts do framework fazem o mesmo cálculo de raiz e sofrem do mesmo problema no layout com pasta de estado.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
