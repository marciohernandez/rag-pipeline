# Backlog: Isolar a carga do .env nos entrypoints

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0012 |
| Status | Captured |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Prontidão de integração |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M01 |
| Criado em | 2026-09-03 |
| Spec promovida | Nenhuma |

## Ideia original

src/config.py chama load_dotenv() no import do módulo. Qualquer teste ou script que importe a configuração injeta o .env inteiro no processo. Isso já quebrou o teste de credencial ausente da SPEC-0003 quando OPENAI_API_KEY foi acrescentada ao .env: o teste passava isolado e falhava na suíte completa. Blindei o teste com monkeypatch, mas a causa continua. Mover a carga para os entrypoints resolveria, mas muda comportamento de produção usado por pipeline.py, search.py e chat.py.

## Problema percebido

load_dotenv() roda no import de src/config.py e injeta o .env da máquina no processo inteiro, criando acoplamento invisível: um teste que prova ausência de credencial depende de qual módulo foi importado antes dele.

## Pessoa afetada ou beneficiada

Quem roda a suíte de testes e quem opera os CLIs da raiz.

## Resultado ou valor esperado

Testes deixam de depender do conteúdo do .env da máquina, sem perder a conveniência nos CLIs, e a regra de configuração injetada do BACKLOG-0011 deixa de ser contornável.

## Contexto

Dívida declarada como bloqueante no BACKLOG-0011 (Pergunta 5, 2026-09-03): precisa ser resolvida antes de src/app/ receber implementação, porque um backend assíncrono chamando o pipeline agravaria o acoplamento de estado global de ambiente.

## Referências relacionadas

- `specs/inbox/2026-09-02-195708-carregar-o-env-nos-entrypoints-em-vez-do-import-de-config.md`: captura de origem, preservada integralmente. Tipo: captura relacionada.
- `specs/backlog/0011-contrato-handoff-projeto-mae.md`: declara este item como dívida bloqueante da fronteira interna entre pipeline e backend de aplicação. Tipo: backlog relacionado.

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
