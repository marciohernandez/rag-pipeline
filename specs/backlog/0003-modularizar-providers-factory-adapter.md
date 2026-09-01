# Backlog: Modularizar providers com Factory e Adapter

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0003 |
| Status | Captured |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Arquitetura de providers |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M0 — Finalizar o componente rag-ingestion-pipeline |
| Criado em | 2026-08-31 |
| Spec promovida | Nenhuma |

## Ideia original

Separar providers de embeddings e bancos vetoriais do módulo monolítico atual usando contratos, Factory e Adapter, definindo o escopo oficial e a paridade esperada.

## Problema percebido

O src/embedder.py concentra condicionais e comportamentos de OpenAI, OpenRouter, Hugging Face, Qdrant, ChromaDB e Pinecone, dificultando segurança, testes e evolução.

## Pessoa afetada ou beneficiada

Mantenedores do componente e equipe responsável pela integração futura.

## Resultado ou valor esperado

Providers podem evoluir e ser testados isoladamente, com comportamento suportado e diferenças explicitamente documentados.

## Contexto

Item P1 do milestone M0, sujeito à decisão posterior sobre providers oficiais e alternativas.

## Referências relacionadas

- `.specsfy/RULES.md`: Factory, Adapter, Strategy e modularidade.
- `.specsfy/STACK.md`: providers e bancos vetoriais implementados.
- `src/embedder.py`: implementação monolítica atual.
- BACKLOG-0001: garantias de segurança que os adapters deverão preservar.
- Linear `LEAD-89`: tracking do item no milestone M0.

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
