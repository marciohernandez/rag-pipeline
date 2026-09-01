---
name: specsfy-specialist-domain-modeling
description: Descobrir e refinar linguagem de domínio, invariantes, eventos, aggregates e boundaries a partir de cenários concretos. Use quando termos, regras ou ownership estiverem ambíguos ou uma decisão de modelo for necessária; não criar documentação paralela à fonte autorizada.
---

# Modelagem de domínio

## Fluxo

1. Identificar atores, objetivos, comandos, fatos e regras.
2. Coletar termos reais e expor sinônimos e colisões.
3. Construir cenários felizes, limites, falhas e tempo.
4. Formular invariantes e owner de cada decisão.
5. Agrupar comportamento por consistência e mudança conjunta.
6. Testar boundaries contra casos que os atravessam.
7. Atualizar glossário, contexto e ADR autorizados.

## Padrões

- Nomear pelo domínio, não pela camada técnica.
- Distinguir entidade, valor, evento e projeção pelo comportamento.
- Manter invariantes junto do owner capaz de garanti-las.
- Não criar aggregate grande por conveniência de consulta.
- Separar bounded contexts quando o mesmo termo tem modelos legítimos distintos.
- Usar eventos no passado e comandos no imperativo.
- Validar o modelo com exemplos e contraexemplos.

## Validação

- Linguagem consistente em spec, código, UI e dados.
- Cenários que exercitam invariantes e transições.
- Ownership sem escrita concorrente indefinida.
- Decisões registradas apenas na fonte autorizada.

Leia [references/standards.md](references/standards.md) para artefatos,
heurísticas e padrões de modelagem.
