# Backlog: Copilot com acesso ao sistema e ao conteúdo processado

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0038 |
| Status | Captured |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-09 |
| Spec promovida | Nenhuma |

## Ideia original

aparentemente tudo funcionando menos o assistente. quando escolho a coleção ( esta como opcional) ele não acessa as informações para responder. eu quero um assistente ( copilot) que tem acesso a todo o sistema, tudo que é feito inclusive as informações que são processadas para envio a base vetorial. assim posso perguntar qualquer coisa que ele respondo. entendeu?

## Problema percebido

O assistente atual é restrito a orientação sobre RAG e pipeline e não oferece consulta abrangente do estado do sistema e do conteúdo processado. A pessoa também relatou que selecionar uma coleção não permite obter respostas sobre suas informações; a causa desse caso ainda não foi reproduzida.

## Pessoa afetada ou beneficiada

Pessoa usuária autenticada do RAG Pipeline.

## Resultado ou valor esperado

Consultar pelo chat as informações do sistema e dos documentos processados para a base vetorial, para responder perguntas sobre o conteúdo e o que acontece no produto.

## Contexto

Em 2026-10-09, durante a conferência final da SPEC-0030, a pessoa pediu: “vamos deixar como backlog sobre o copilot...e continuar o desenvolvimento. qual o proximo passo?”. Registrar para evolução futura, sem implementar agora. A SPEC-0021 entregou orientação especializada em RAG; a SPEC-0030 troca Bases por Coleções. A ampliação de copilot é independente do fechamento da SPEC-0030. O relato de consulta da coleção deve ser verificado contra o comportamento já contratado antes do Delivery Gate.

## Referências relacionadas

- `specs/completed/0021-chat-assistente-especialista-rag-pipeline/spec.md` — spec relacionada: assistente atual, especializado em orientação sobre RAG.
- `specs/in-progress/0030-colecoes-por-workspace-com-envios-acumulados/spec.md` — spec relacionada: consulta de coleção no assistente (FR-013, AC-016).
- `specs/backlog/0022-chat-com-assistente-llm-para-ajudar-no-uso-do-sistema.md` — precedente promovido; este item amplia o acesso às informações do produto.
- `src/pipeline/assistant.py` e `src/app/routers/assistente.py` — fontes técnicas: prompt restrito e recuperação da coleção selecionada.

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

- Decisão da pessoa em 2026-10-09: manter a evolução do copilot no backlog e continuar o desenvolvimento atual.
- Aberto: detalhar acesso a conteúdo antes da publicação, fontes disponíveis, permissões e critérios de aceite.
- Relato de consulta da coleção ainda sem reprodução; não atribuir sua causa somente ao prompt.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Manter capturado para retomada futura. Não iniciar refinamento ou implementação do copilot nesta entrega, conforme pedido da pessoa.
