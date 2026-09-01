# Backlog: Compatibilizar o contrato Markdown do projeto-mãe

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0002 |
| Status | Captured |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Contrato de integração Markdown |
| Tipo | Técnico |
| Prioridade | P0 — urgente |
| Milestones | M0 — Finalizar o componente rag-ingestion-pipeline |
| Criado em | 2026-08-31 |
| Spec promovida | Nenhuma |

## Ideia original

Preservar metadados recebidos do rag-pipeline, incluindo document_id, tenant_id, type, version e status, e tratar documentos de perguntas e respostas separados por ---.

## Problema percebido

A identidade atual sobrescreve document_id e o chunking não possui contrato explícito para tenant nem para o formato Q&A do projeto-mãe.

## Pessoa afetada ou beneficiada

Equipe que integrará o rag-ingestion-pipeline ao rag-pipeline e operadores de bases multi-tenant.

## Resultado ou valor esperado

Documentos validados pelo projeto-mãe entram no componente sem perda semântica de identidade, escopo ou estrutura Q&A.

## Contexto

Item P0 do milestone M0, limitado à preparação de compatibilidade futura sem implementar a V1 do projeto-mãe.

## Referências relacionadas

- `PROJECT.md`: fronteira entre o componente e o projeto-mãe.
- `.specsfy/DATABASE.md`: identidades e ausência atual de tenant persistente.
- `src/identity.py`, `src/loader.py` e `src/chunker.py`: contrato implementado hoje.
- Fontes fornecidas do projeto-mãe: `briefing.md`, `tech_stack.md` e constituição 1.2.1.
- Linear `LEAD-86`: tracking do item no milestone M0.

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
