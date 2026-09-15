# Backlog: Decidir onde o resumo de seção vive e revisar as regras de corte do chunker

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0016 |
| Status | Captured |
| Produto | RAG Pipeline SaaS |
| Épico | M02 — Elevar a confiança na qualidade da recuperação |
| Funcionalidade | Estratégia de chunking e resumo de seção |
| Tipo | Técnico |
| Prioridade | Não priorizado |
| Milestones | M02 |
| Criado em | 2026-09-15 |
| Spec promovida | Nenhuma |

## Ideia original

Captura de 2026-09-03 (reanalisar-a-quebra-de-chunks-e-onde-o-resumo-deve-viver): "Muito importante, agora vamos guardar essa informação pra ver depois é criar um backlog. A gente precisa reanalisar toda a parte de quebra de tanques e as características pra gente não ter problema na quebra de tanque. E também a gente deve. Vê a melhor forma de utilizar que o sistema ele cria um resumo, só que sem resumos transformou em um tanque isolado. E eu preciso ver como que é melhor essas informação estarem de repente com um metadado, num chunk ou algo parecido. E algo que precisa ser estudado ai." Complementada pela análise da captura de 2026-09-01 (usar-resumos-de-secao-para-melhorar-a-recuperacao): o campo Texto original dessa captura preserva um fragmento sobre outro assunto (lista de documentos .md no mockup); a analise de resumo de secao ali registrada e tratada como valida por decisao de Marcio em 2026-09-15, com a inconsistencia do campo registrada como nota de proveniencia.

## Problema percebido

A busca plana atual faz resumos de seção competirem com chunks detalhados na mesma recuperação, sem aproveitar sua estrutura como índice navegacional (chunk_type: section_summary concatenado à lista de chunks detalhados em src/pipeline/chunker.py:148-232). As regras de corte/tamanho do chunker têm pontos que hoje só geram alerta heurístico em src/pipeline/quality.py (perda de estrutura de títulos, truncamento de frase, texto colapsado, conteúdo útil curto, distribuição de tamanho), sem que exista uma decisão sobre quando isso deveria mudar de comportamento.

## Pessoa afetada ou beneficiada

Marcio e a equipe de consultoria que opera e audita a recuperação do RAG Pipeline.

## Resultado ou valor esperado

Uma decisão registrada sobre onde o resumo de seção deve viver (metadado, chunk com peso diferenciado na busca, ou índice de roteamento separado da busca principal) e quais regras de corte/tamanho do chunker devem mudar, com a prova mínima necessária para sustentar a decisão — sem comprometer ainda a implementação final, que fica na spec seguinte.

## Contexto

Primeira das duas specs candidatas da M02 (specs/milestones/M02.md), aberta na entrevista de roadmap de 2026-09-15. Não cobre detecção de contradição ou duplicação entre documentos diferentes (fora deste componente, limite declarado em PROJECT.md) nem a medição final via validate.py (fica para a segunda spec candidata, que só abre depois desta decidir algo concreto).

## Referências relacionadas

- `specs/inbox/2026-09-03-072811-reanalisar-a-quebra-de-chunks-e-onde-o-resumo-deve-viver.md` — captura de origem, formulação literal preservada. Tipo: origem.
- `specs/inbox/2026-09-01-201529-usar-resumos-de-secao-para-melhorar-a-recuperacao.md` — captura de origem complementar; ver nota de proveniência na "Ideia original" sobre a inconsistência do campo Texto original. Tipo: origem.
- `specs/milestones/M02.md` — marco que abriu este item e define a condição de saída e o que fica fora de escopo. Tipo: milestone.
- `specs/backlog/0005-gate-qualidade-chunks-metadados.md:344-347` (promovido à SPEC-0006, `Complete`) — já registrou este exato risco de fronteira em 2026-09-01: "a captura de 2026-09-03 pode mudar a estratégia de quebra e transformar o `section_summary` em metadado. Se isso for decidido antes desta fatia ser implementada, o recorte por `chunk_type` do relatório precisa ser revisto." A SPEC-0006 já foi entregue medindo a quebra sem alterá-la; este item pode exigir revisão do agrupamento por `chunk_type` em `src/pipeline/quality.py`. Tipo: spec relacionada, risco antecipado.
- `src/pipeline/chunker.py:148-232` (`_section_summary_chunks`) — superfície de código que materializa hoje o `chunk_type: "section_summary"` concatenado aos chunks detalhados. Tipo: superfície afetada.
- `src/pipeline/quality.py` — sinais heurísticos hoje somente informativos (perda de estrutura, truncamento, texto colapsado, conteúdo curto, distribuição de tamanho) que este item pode decidir promover a bloqueio ou alterar. Tipo: superfície afetada.
- `src/pipeline/validation.py` / `validate.py` — instrumento de medição que a spec seguinte (BACKLOG-0017) usará para comparar antes/depois; esta spec não executa a medição. Tipo: dependência futura.

## Comportamento esperado

A esclarecer.

## Regras de negócio

- A esclarecer conforme risco e complexidade.

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado.

## Qualidades e operação

- Segurança: a avaliar.
- Privacidade: a avaliar.
- Desempenho e volume: a avaliar.
- Auditoria e observabilidade: a avaliar.

## Dependências

- Nenhuma registrada.

## Situações de erro

- A esclarecer.

## Escopo

- Dentro: a esclarecer.
- Fora: a esclarecer.

## Dúvidas, decisões e riscos

- Nenhum registrado.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
