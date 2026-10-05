# Backlog: Memória de longo prazo do assistente por pessoa

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0027 |
| Status | Refining |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-09-28 |
| Spec promovida | Nenhuma |

## Ideia original

Memória de longo prazo do assistente de chat (atravessa conversas diferentes, guardando preferências e fatos conversados antes, nos moldes da memória do Claude), extraída como item próprio a partir da fatia 2 registrada em BACKLOG-0022 e explicitamente deixada fora de escopo pela SPEC-0021 (fatia 1, já entregue e mesclada em main).

## Problema percebido

Hoje o assistente (SPEC-0021) só tem memória de curto prazo, restrita à mesma conversa (20 mensagens). A pessoa precisa repetir preferências e fatos já conversados antes toda vez que abre uma nova conversa, porque nada é lembrado entre conversas diferentes.

## Pessoa afetada ou beneficiada

Pessoa autenticada (owner, admin ou member) que já usa o assistente do BACKLOG-0022/SPEC-0021 e conversa com ele em mais de uma sessão ao longo do tempo.

## Resultado ou valor esperado

O assistente usa preferências e fatos já conversados antes sem a pessoa precisar repeti-los em uma nova conversa, e a pessoa consegue visualizar e apagar individualmente os itens de memória guardados sobre ela.

## Contexto

Esta é a fatia 2 de BACKLOG-0022 (specs/backlog/0022-chat-com-assistente-llm-para-ajudar-no-uso-do-sistema.md), que já registra escopo, critérios de aceite e decisões para esta fatia mas a deixou de fora da especificação inicial. SPEC-0021 (specs/completed/0021-chat-assistente-especialista-rag-pipeline/spec.md) entregou só a fatia 1 (memória de curto prazo) e registrou explicitamente que a memória de longo prazo 'vira item de backlog próprio'. O bloqueio original — BACKLOG-0023 (autenticação real por pessoa) — já foi concluído (SPEC-0020, mesclada em main), então este item está pronto para aprofundamento e especificação.

## Referências relacionadas

- `specs/backlog/0022-chat-com-assistente-llm-para-ajudar-no-uso-do-sistema.md` — item de origem; já registra escopo, critérios de aceite e decisões da fatia 2, aqui extraídos para um item próprio. Tipo: backlog relacionado (origem direta).
- `specs/completed/0021-chat-assistente-especialista-rag-pipeline/spec.md` — spec que entregou a fatia 1 (memória de curto prazo) e deixou a memória de longo prazo explicitamente fora de escopo, remetendo a este item (seção 3, "Fora de escopo"; dúvida respondida na seção de pesquisa; US-005). Tipo: spec relacionada (predecessora, define a base sobre a qual esta fatia se apoia: painel, conversas, mensagens, contrato de LLM).
- `specs/completed/0020-autenticacao-real-por-pessoa/spec.md` (BACKLOG-0023) — autenticação real por pessoa, bloqueio original desta fatia, já concluída e mesclada em `main`. Tipo: spec relacionada (dependência agora resolvida).

## Comportamento esperado

- Memória de longo prazo por pessoa individual (não por tenant/projeto), atravessando conversas diferentes — nos moldes da memória do Claude: preferências e fatos conversados antes ficam disponíveis em uma nova conversa, sem a pessoa precisar repeti-los.
- A pessoa consegue visualizar e apagar individualmente os itens de memória guardados sobre ela (controle de privacidade já decidido em BACKLOG-0022).
- Mantém as restrições já vigentes na fatia 1: o assistente continua só orientando/recomendando, sem executar ações no sistema em nome da pessoa.

## Regras de negócio

- A esclarecer conforme risco e complexidade (ex.: o que exatamente vira memória, quando é criada/atualizada/expira).

## Critérios de aceitação

- **Dado** um assistente com memória de longo prazo, **quando** a pessoa pergunta em uma nova conversa algo relacionado a uma preferência ou fato já conversado antes, **então** o assistente usa essa memória sem repetir a pergunta. (Herdado de BACKLOG-0022.)
- **Dado** itens de memória de longo prazo guardados sobre a pessoa, **quando** ela acessa a área de memória, **então** consegue visualizar e apagar itens individuais guardados sobre ela. (Herdado de BACKLOG-0022.)
- **Dado** qualquer resposta do assistente com memória de longo prazo ativa, **quando** ele responde, **então** continua sem executar nenhuma ação no sistema (criar/alterar/apagar Workspace, Base, execução ou configuração). (Herdado da restrição vigente em SPEC-0021 e BACKLOG-0022.)

## Qualidades e operação

- Segurança: a avaliar na especificação (mesmo isolamento por pessoa/tenant/projeto já usado em SPEC-0021 para conversas e mensagens de curto prazo).
- Privacidade: a pessoa deve conseguir ver e apagar itens de memória de longo prazo guardados sobre ela (decisão já confirmada em BACKLOG-0022); conteúdo enviado ao provider de LLM configurado segue o mesmo padrão já aceito por `chat.py` e por SPEC-0021.
- Desempenho e volume: a avaliar na especificação.
- Auditoria e observabilidade: a avaliar na especificação.

## Dependências

- `specs/completed/0020-autenticacao-real-por-pessoa/spec.md` (BACKLOG-0023) — não é mais bloqueante: já concluída e mesclada em `main`. Registrada aqui só para rastreabilidade da decisão original.

## Situações de erro

- A esclarecer.

## Escopo

- Dentro: memória de longo prazo por pessoa individual, atravessando conversas diferentes (preferências e fatos conversados antes); tela/área para a pessoa visualizar e apagar itens de memória guardados sobre ela.
- Fora: qualquer ação do assistente sobre o sistema (criar, alterar ou apagar Workspace, Base, execução ou configuração) — mesma restrição da fatia 1; escolha do provider de LLM em si (depende de BACKLOG-0010); tudo o que já foi entregue na fatia 1 (SPEC-0021): chat multi-página, histórico de conversas, memória de curto prazo, análise de Base apontada.

## Dúvidas, decisões e riscos

- **Decisão** (herdada de BACKLOG-0022): a memória de longo prazo é por pessoa individual, não por tenant/projeto.
- **Decisão** (herdada de BACKLOG-0022): a pessoa tem controle de visualizar e apagar itens de memória guardados sobre ela.
- **Decisão** (herdada de BACKLOG-0022 e SPEC-0021): o assistente continua só orientando/recomendando nesta fatia também — sem executar ações no sistema.
- **Aberto** (herdado de BACKLOG-0022): formato de armazenamento e extração de memória de longo prazo — que tipo de fato/preferência vira memória e como é resumido/extraído das conversas. Fica para a especificação.
- **Aberto**: quais papéis (owner/admin/member) têm acesso à área de visualizar/apagar memória — SPEC-0021 assumiu "todos" para o chat em si; a confirmar se a área de memória segue a mesma regra.
- **Risco** (herdado de BACKLOG-0022): a extração automática de "fatos e preferências" de conversas livres pode captar informação sensível ou incorreta; a especificação precisa decidir controle e revisão antes de persistir.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras (acesso à área de memória por papel ainda a confirmar; regras de extração/expiração da memória ainda a esclarecer).
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco (privacidade já decidida; segurança e desempenho a aprofundar na especificação).
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Bloqueio original (BACKLOG-0023) resolvido. Pronto para aprofundamento adicional sobre permissões e formato de extração/expiração de memória, e em seguida `$specsfy-03-specify`.
