# Backlog: Autenticação real por pessoa

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0023 |
| Status | Captured |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-09-18 |
| Spec promovida | Nenhuma |

## Ideia original

Sem citação literal própria: item derivado da descoberta de BACKLOG-0022 (chat com assistente LLM), que exige memória de longo prazo por identidade individual de pessoa. Hoje a autenticação (src/app/auth.py) é um token estático de demonstração (SPEC-0012, DEC-002) com Identity(tenant_id, project_id, role); não existe conceito de pessoa individual dentro de um tenant/projeto.

## Problema percebido

Identity(tenant_id, project_id, role) identifica um papel dentro de um tenant/projeto, mas não distingue uma pessoa da outra quando ambas têm o mesmo papel no mesmo tenant/projeto. Qualquer capacidade que precise saber 'de quem' é uma preferência, uma memória, uma ação ou uma autoria — como a memória de longo prazo pedida em BACKLOG-0022 — não tem hoje onde se apoiar.

## Pessoa afetada ou beneficiada

Pessoas usuárias que compartilham tenant/projeto/papel e precisam ser distinguidas entre si; indiretamente, qualquer fatia futura que dependa de identidade individual (auditoria por pessoa, preferências, memória, autoria de ações).

## Resultado ou valor esperado

Um modelo de identidade que reconhece pessoas individuais (cadastro e/ou login real), preservando o isolamento por tenant/projeto e os papéis (owner/admin/member) já estabelecidos, e substituindo o token estático de demonstração como identidade primária do produto.

## Contexto

Nasce como pré-requisito bloqueante de BACKLOG-0022 (chat com assistente LLM especializado em RAG), que decidiu que a memória de longo prazo do assistente deve ser por pessoa, não por tenant/projeto. Reabre uma decisão que SPEC-0012 (DEC-002) havia deixado explicitamente fora de escopo ('token estático de demonstração' como aceitável para aquela fatia). Afeta o produto inteiro, não só o chat: qualquer spec que hoje usa Identity(tenant_id, project_id, role) precisa ser revisitada para saber se e como incorpora a pessoa individual.

## Referências relacionadas

- `specs/backlog/0022-chat-com-assistente-llm-para-ajudar-no-uso-do-sistema.md` — item que originou esta dependência; sua memória de longo prazo por pessoa só pode ser implementada depois deste. Tipo: dependente (bloqueado por este item).
- `src/app/auth.py` — implementação atual do token estático de demonstração e de `Identity(tenant_id, project_id, role)`. Tipo: superfície técnica afetada.
- `specs/defined/` e specs concluídas que usam `Identity`/`require_write_role` (SPEC-0012 em diante) — todas assumem hoje que papel identifica a parte que age; precisam ser revisitadas quanto à compatibilidade com pessoa individual. Tipo: superfície de produto afetada.

**Nota de numeração**: SPEC-0019 (seção 2 e 3) cita um "item de backlog 0023" ainda não criado para campos de estratégia de chunking (splitter, tamanho, overlap) na interface de upload. Este BACKLOG-0023 é uma coisa diferente (autenticação por pessoa); aquele item de chunking, quando criado, deve receber outro número (0024 em diante) e a referência em SPEC-0019 precisa ser corrigida para não apontar para este item por engano.

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
