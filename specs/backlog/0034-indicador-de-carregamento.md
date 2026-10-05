# Backlog: Indicador de carregamento junto da ação ou área em processamento

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0034 |
| Status | Promoted |
| Produto | RAG Pipeline |
| Épico | Experiência de uso |
| Funcionalidade | Feedback de processamento |
| Tipo | Melhoria |
| Prioridade | Segunda na ordem confirmada pelo usuário |
| Milestones | |
| Criado em | 2026-10-05 |
| Spec promovida | SPEC-0025 — specs/completed/0025-indicador-de-carregamento/spec.md |

## Ideia original

sempre que estiver executando algo aparecer a imagem de um circulo rodando para indicar que esta sendo processa algo.

## Problema percebido

Esperas de operações na interface nem sempre exibem um círculo de carregamento.

## Pessoa afetada ou beneficiada

Pessoas usuárias autenticadas e pessoas que entram no sistema.

## Resultado ou valor esperado

Perceber que a operação está em andamento sem bloquear o restante da tela.

## Contexto

Escolha confirmada na conversa: círculo junto da ação ou área em processamento. Reutilizar Spinner existente e preservar Claro, Escuro e Sistema.

## Referências relacionadas

- Origem: specs/inbox/2026-10-05-170632-indicador-de-carregamento-circulo-girando-durante-qualquer-processamento.md.
- Spec relacionada: SPEC-0024, preservação de temas.
- Documentação relacionada: INTERFACE.md, Spinner/Button e estados locais existentes.

## Comportamento esperado

Círculo junto da ação ou área enquanto houver espera, sem bloqueio global.

## Regras de negócio

- Preservar permissões e estados de erro; indicador termina com a operação.

## Critérios de aceitação

- Given uma operação pendente, When a tela é apresentada, Then há círculo local e texto.
- Given uma operação pendente, When termina com sucesso ou erro, Then seu círculo sai.
- Given preferência de movimento reduzido, When há espera, Then texto permanece e rotação para.

## Qualidades e operação

- Segurança e privacidade: sem nova API, dado persistente ou permissão.
- Desempenho: reutilizar estados atuais; não adicionar polling.
- Auditoria: provas de componentes e revisão visual na spec.

## Dependências

- Primitives locais e tema SPEC-0024.

## Situações de erro

- Remover o indicador na falha, manter mensagem e recuperação existentes.

## Escopo

- Dentro: esperas de telas atuais, inclusive indexação e assistente.
- Fora: overlay global, nova operação e percentual fictício.

## Dúvidas, decisões e riscos

- Escolha confirmada: opção 1 — junto da ação/área, restante disponível.
- Nenhuma lacuna aplicável; requisitos canônicos passaram à SPEC-0025.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Consultar a fonte normativa SPEC-0025; backlog preserva a proveniência.
