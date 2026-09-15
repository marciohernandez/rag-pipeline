# Backlog: Decidir onde o resumo de seção vive e revisar as regras de corte do chunker

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0016 |
| Status | Ready for specification |
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

1. A spec implementa, de forma mínima (protótipo, não necessariamente o
   código de produção final), as três alternativas de colocação do resumo de
   seção discutidas na descoberta:
   - (a) resumo como metadado anexado a cada chunk detalhado da mesma seção,
     sem virar documento próprio na busca;
   - (b) resumo continua chunk indexado, com peso/sinal que evita competir em
     pé de igualdade com chunks detalhados;
   - (c) resumo sai da coleção principal e vira índice de roteamento
     hierárquico (busca a seção pelo resumo, depois recupera os chunks
     detalhados daquela seção).
2. Cada alternativa é rodada contra o gabarito real de
   `documentos/vivo_gold_banda_larga_pf/consultas.yaml` (10 consultas, base
   pequena — o protótipo usa o gabarito inteiro, não uma amostra reduzida),
   usando `validate.py`/`validation.py` como instrumento de leitura, sem
   alterar a base indexada de produção.
3. O resultado da comparação é registrado (aprovações por categoria, ruído
   percebido) e a spec decide qual alternativa vence, ou se nenhuma supera o
   comportamento atual — nesse caso a decisão documentada pode ser "manter
   como está", com a justificativa.
4. A decisão inclui também quais regras de corte/tamanho do chunker mudam em
   consequência direta da alternativa escolhida (ex.: limite de tamanho do
   chunk de resumo, critério `section_summary_min_children`). Sinais
   heurísticos de `quality.py` sem relação com a colocação do resumo
   (duplicata exata, texto colapsado, truncamento de frase não ligado a
   resumo) não são tocados por esta spec.
5. Se a alternativa escolhida mudar a semântica de `chunk_type` usada hoje
   pelo agrupamento do relatório de qualidade (`src/pipeline/quality.py`,
   risco antecipado por BACKLOG-0005/SPEC-0006), a decisão registra
   explicitamente se esse agrupamento precisa ser revisto — a revisão em si
   fica para BACKLOG-0017 ou spec própria, não para esta.

## Regras de negócio

- A decisão final é registrada na própria spec (seção de decisões), não em
  documento paralelo.
- A comparação usa sempre o gabarito versionado já existente para a base —
  não inventa casos de teste sintéticos como critério de aceite principal.
- Nenhuma execução desta spec grava em Qdrant de produção nem altera bases já
  indexadas; o protótipo roda isolado (ex.: `InMemoryVectorStoreAdapter` ou
  execução local descartável).

## Critérios de aceitação

- Given as três alternativas de colocação do resumo implementadas como
  protótipo, when cada uma é avaliada contra o gabarito de
  `vivo_gold_banda_larga_pf/consultas.yaml`, then a spec registra, para cada
  alternativa, quantas consultas do gabarito são aprovadas e algum indício de
  ruído (ex.: resumo aparecendo como resultado quando um chunk detalhado seria
  mais útil).
- Given o resultado da comparação, when nenhuma alternativa supera claramente
  o comportamento atual, then a decisão documentada é "manter como está" com a
  justificativa registrada, em vez de escolher uma alternativa sem evidência.
- Given a alternativa escolhida, when ela implica mudança em regra de
  corte/tamanho do chunker, then a spec lista exatamente quais parâmetros de
  `chunker.py` mudam e qual o novo comportamento esperado.
- Given a decisão registrada, when ela afeta o agrupamento por `chunk_type`
  hoje usado pelo relatório de `quality.py`, then a spec sinaliza essa
  dependência explicitamente para a spec seguinte (BACKLOG-0017), sem
  implementar a correção do relatório aqui.

## Qualidades e operação

- Segurança: não aplicável — não há dado novo, credencial ou superfície de
  autenticação envolvida.
- Privacidade: não aplicável — usa a mesma base de demonstração já versionada
  no repositório (`documentos/vivo_gold_banda_larga_pf/`).
- Desempenho e volume: não é objetivo desta spec; a base de comparação é
  pequena (10 consultas, 8 documentos) de propósito, para manter o protótipo
  rápido. Desempenho em escala fica para BACKLOG-0017, se aplicável.
- Auditoria e observabilidade: a decisão e a comparação numérica ficam
  registradas na própria spec (seções de tarefas/evidência), sem exigir novo
  mecanismo de log.

## Dependências

- Nenhuma bloqueante. Usa `src/pipeline/chunker.py`, `src/pipeline/quality.py`
  e `src/pipeline/validation.py`/`validate.py`, já entregues pelo M01, e a
  base+gabarito já versionados em `documentos/vivo_gold_banda_larga_pf/`.

## Situações de erro

- Se o gabarito de `vivo_gold_banda_larga_pf/consultas.yaml` não cobrir casos
  suficientes para diferenciar as três alternativas (ex.: nenhuma consulta
  toca seções com resumo), a spec registra essa limitação como decisão aberta
  em vez de forçar uma escolha sem evidência.
- Se as três alternativas empatarem tecnicamente, a decisão documentada
  prioriza a alternativa de menor custo de implementação para BACKLOG-0017,
  com a justificativa registrada.

## Escopo

- Dentro: comparar as três alternativas de colocação do resumo de seção;
  decidir qual vence (ou manter como está); decidir quais regras de
  corte/tamanho do chunker mudam em consequência direta dessa decisão;
  sinalizar impacto sobre o agrupamento por `chunk_type` em `quality.py`.
- Fora: implementação final de produção (BACKLOG-0017); medição completa
  sobre a base inteira ou outras bases; detecção de contradição/duplicação
  entre documentos diferentes (fora do componente, `PROJECT.md`); promover
  qualquer sinal heurístico de `quality.py` a bloqueio, quando não ligado à
  colocação do resumo; ingestão multi-formato.

## Dúvidas, decisões e riscos

- **Decisão (Pergunta 1 da descoberta):** a spec compara as três alternativas
  com dado real em vez de escolher uma por texto a priori.
- **Decisão (Pergunta 2 da descoberta):** "revisar regras de corte" cobre
  apenas os parâmetros que mudam por causa da colocação do resumo; sinais
  heurísticos de `quality.py` sem relação com resumo não são tocados aqui.
- **Decisão (Pergunta 3 da descoberta):** a prova mínima é um protótipo rápido
  rodado contra o gabarito real de `vivo_gold_banda_larga_pf`, não a medição
  completa (que fica para BACKLOG-0017) nem só raciocínio sem dado.
- **Risco herdado de BACKLOG-0005/SPEC-0006:** a decisão pode exigir revisão
  do agrupamento por `chunk_type` no relatório de qualidade — registrado como
  dependência para a spec seguinte, não resolvido aqui.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
