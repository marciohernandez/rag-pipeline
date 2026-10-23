# Backlog: CI: limite de tempo e nova tentativa no passo de instalação do apt

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0049 |
| Status | Promoted |
| Produto | RAG Pipeline |
| Épico | Esteira de integração contínua |
| Funcionalidade | Resiliência do passo de instalação de pacotes do sistema no CI |
| Tipo | Técnico |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-23 |
| Spec promovida | specs/draft/0044-ci-limite-de-tempo-e-nova-tentativa-no-apt/spec.md |

## Ideia original

eu sempre fico com esse teste pendente, tem algo errado (CI do GitHub: job "Ruff and Pytest" fica pendente por muito tempo; ocorreu nos PRs #77, #78 e #81)

## Problema percebido

O passo Install system packages for document conversion (apt-get de tesseract e libreoffice) às vezes leva 15 a 30 minutos, contra cerca de 1 minuto normal. O job fica pendente, e a main exige o check Ruff and Pytest para o merge.

## Pessoa afetada ou beneficiada

Quem abre PRs e espera o CI liberar o merge.

## Resultado ou valor esperado

CI previsível: o passo do apt é cancelado após 5 minutos e tentado de novo até 3 vezes, e o job tem teto de 25 minutos, sem cancelar nem reexecutar à mão.

## Contexto

Inbox: specs/inbox/2026-10-23-130907-ci-trava-no-passo-de-instalacao-de-pacotes-do-sistema-apt.md. Workflow: .github/workflows/ci.yml. Spec relacionada: SPEC-0007 (esteira de CI), cujo texto diz que não há retry automático.

Observado em 2026-10-23 nos logs: no PR #78 o passo levou cerca de 16 minutos (12:49 a 13:05 UTC), e no PR #81 ficou 15 minutos no mesmo passo (13:45 a 14:00 UTC). O pytest e o Ruff não foram a causa. As execuções boas levam cerca de 6 minutos no job inteiro. Nos três casos o contorno foi `gh run cancel` e `gh run rerun`, e a segunda tentativa passou.

## Referências relacionadas

- `specs/inbox/2026-10-23-130907-ci-trava-no-passo-de-instalacao-de-pacotes-do-sistema-apt.md` (origem; não alterada).
- Spec relacionada: `specs/completed/0007-ruff-e-esteira-de-integracao-continua/spec.md` (define o `ci.yml`; registra a regra confirmada de rodar Ruff e Pytest a cada push de branch de fase e em pull request, e afirma que não há retry automático).
- Documentação relacionada: `.specsfy/RULES.md`, seção Testes (regra do workflow de integração contínua).
- Teste relacionado: `tests/test_ci_gates.py` (confere o workflow).
- Sem duplicata encontrada.

## Comportamento esperado

Declarado nas respostas da pessoa (2026-10-23):

1. **Alcance (Pergunta 1):** limite de tempo e nova tentativa no passo do apt, mantendo os gatilhos de push e de pull request como estão.
2. **Limite do passo (Pergunta 2):** 5 minutos por tentativa, com até 3 tentativas.
3. **Teto do job (Pergunta 3):** 25 minutos para o job "Ruff and Pytest".

## Regras de negócio

- Declarado: os gatilhos de push e pull request não mudam, conforme a regra confirmada da SPEC-0007.
- Declarado: os comandos de Ruff e Pytest não mudam.
- Inferência: a nova tentativa vale só para o passo do apt, nunca para o Pytest, para não esconder teste instável.
- Inferência: as actions continuam fixadas por SHA e o workflow não recebe segredo (PR-006 e FR-003 da SPEC-0007).

## Critérios de aceitação

- Dado que o apt demora mais de 5 minutos, quando a tentativa estoura o limite, então ela é cancelada e o passo tenta de novo, até 3 vezes.
- Dado que as 3 tentativas falham, então o job falha com mensagem legível e o merge fica bloqueado.
- Dado que o job ultrapassa 25 minutos por qualquer motivo, então o GitHub o cancela.
- Dado um push ou um pull request, então o CI continua rodando Ruff e Pytest como hoje.
- Dado o workflow, então `tests/test_ci_gates.py` confere o limite do passo, a nova tentativa e o teto do job.

## Qualidades e operação

- Segurança: o workflow continua sem segredo e com actions fixadas por SHA.
- Privacidade: não se aplica.
- Desempenho e volume: pior caso do passo de 15 minutos (3 x 5); job com teto de 25 minutos; execuções boas continuam em cerca de 6 minutos.
- Auditoria e observabilidade: a falha após as 3 tentativas precisa ser legível no registro do job.

## Dependências

- SPEC-0007 (esteira de CI), entregue.
- Regra do `.specsfy/RULES.md` sobre o workflow de CI.

## Situações de erro

- As 3 tentativas do apt falham: o job falha e o merge fica bloqueado; a reexecução manual continua possível.
- O job passa de 25 minutos por outro passo: cancelado pelo teto.
- Observação: a nova tentativa não deve repetir o Pytest.

## Escopo

- Dentro: `.github/workflows/ci.yml` (passo do apt e teto do job "Ruff and Pytest") e o teste do workflow em `tests/test_ci_gates.py`.
- Fora: mudar os gatilhos de push e pull request; cache dos pacotes do apt; o job do frontend; código da aplicação.

## Dúvidas, decisões e riscos

- Decisões confirmadas em 2026-10-23: Perguntas 1 a 3, na seção "Comportamento esperado".
- Aberto, não bloqueante: a frase "não há retry automático" da SPEC-0007 passa a divergir da prática. Proposta: spec nova que referencia a SPEC-0007, sem reabrir uma spec concluída.
- Suposição: a lentidão vem do espelho de pacotes do Ubuntu e a nova tentativa recupera a maioria dos casos.
- Risco: a correção passa pelo próprio CI, então pode travar enquanto é entregue; mitigado pelo contorno manual já usado.
- Risco: o limite de 5 minutos pode cancelar uma instalação lenta que terminaria; aceito pela pessoa.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promovido a `SPEC-0044` em 2026-10-23; a spec passa a governar o comportamento.
