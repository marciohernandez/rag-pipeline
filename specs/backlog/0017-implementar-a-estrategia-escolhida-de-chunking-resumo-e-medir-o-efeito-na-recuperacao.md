# Backlog: Implementar a estrategia escolhida de chunking/resumo e medir o efeito na recuperacao

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0017 |
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

Sem citacao literal propria: item derivado da entrevista de roadmap da M02 (specs/milestones/M02.md, 2026-09-15), como segunda spec candidata em sequencia a BACKLOG-0016. Motivado pela intencao registrada na captura de 2026-09-01 (usar-resumos-de-secao-para-melhorar-a-recuperacao) de usar resumos de secao como apoio a recuperacao, e pelo pedido de 2026-09-03 de nao ter problema na quebra.

## Problema percebido

Depois que BACKLOG-0016 decidir onde o resumo de secao deve viver e quais regras de corte mudam, falta materializar essa decisao no chunker/indexacao e provar que ela de fato melhora ou preserva a recuperacao, em vez de apenas mudar a estrutura sem medir o efeito.

## Pessoa afetada ou beneficiada

Marcio e a equipe de consultoria que opera e audita a recuperacao do RAG Pipeline.

## Resultado ou valor esperado

A estrategia escolhida implementada em src/pipeline/chunker.py (e onde mais a decisao exigir) e uma medicao comparativa via validate.py sobre a mesma base real, mostrando mais casos corretos no gabarito (ou os mesmos casos com menos ruido) sem regressao em nenhum caso que ja passava antes da mudanca.

## Contexto

Segunda das duas specs candidatas da M02 (specs/milestones/M02.md). Depende de BACKLOG-0016 chegar a uma decisao concreta; nao abre antes disso. Nao cobre deteccao de contradicao entre documentos (fora deste componente) nem ingestao multi-formato.

## Referências relacionadas

- `specs/backlog/0016-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker.md` — pré-requisito direto; esta spec só abre depois que aquela decidir algo concreto. Tipo: dependência.
- `specs/milestones/M02.md` — marco que abriu este item e define a condição de saída. Tipo: milestone.
- `specs/inbox/2026-09-01-201529-usar-resumos-de-secao-para-melhorar-a-recuperacao.md` — motivação de fundo (ver ressalva de proveniência registrada em BACKLOG-0016). Tipo: origem indireta.
- `src/pipeline/validation.py` e `validate.py` — instrumento de medição a ser usado para a comparação antes/depois exigida por esta spec. Tipo: superfície afetada.
- `src/pipeline/chunker.py` — superfície de código onde a decisão de BACKLOG-0016 será materializada. Tipo: superfície afetada.

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

- **Aberto:** o escopo completo desta spec (o que muda em `chunker.py`/`indexing.py`, quais casos do gabarito são afetados) só pode ser refinado depois que BACKLOG-0016 registrar sua decisão; este item permanece `Captured` até então.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
