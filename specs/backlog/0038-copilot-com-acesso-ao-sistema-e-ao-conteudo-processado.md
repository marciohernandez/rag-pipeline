# Backlog: Copilot com acesso ao sistema e ao conteúdo processado

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0038 |
| Status | Promoted |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-09 |
| Spec promovida | specs/draft/0031-copilot-com-acesso-ao-sistema-e-ao-conteudo-processado/spec.md (SPEC-0031) |

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

- A pessoa pergunta qualquer coisa sobre o produto e o copilot responde com base em três fontes: (a) conteúdo indexado de todas as coleções do Workspace; (b) estado operacional (coleções, documentos, envios e status, falhas, execuções, configurações); (c) o Markdown e os metadados processados antes da publicação.
- O seletor de coleção deixa de ser necessário: o copilot busca em todas as coleções do Workspace e o seletor vira filtro opcional para focar a pergunta.
- Toda resposta traz fontes clicáveis (documento, coleção, envio ou tela de origem). Sem base para responder, o copilot diz que não encontrou, sem inventar.
- O copilot só consulta e sugere: indica o passo ou o link da tela, e quem executa é a pessoa.

## Regras de negócio

- O copilot herda o Workspace e o papel de quem pergunta; nunca mostra dados de outro Workspace nem o que o papel não alcança.
- Inferência a confirmar: nunca expõe credenciais de conexão, nem para admin.
- O worker passa a persistir o Markdown processado e seus metadados por documento. Uma versão por documento: nova versão substitui a anterior, e apagar o documento ou a coleção apaga esse material.
- Sem ações de escrita nesta entrega.

## Critérios de aceitação

- Dado um Workspace com coleções indexadas, quando a pessoa pergunta sobre o conteúdo sem selecionar coleção, então a resposta cita a fonte (documento e coleção) com link.
- Dado um envio com falha, quando a pessoa pergunta por que falhou, então o copilot responde com o estado do envio e sugere a ação (Repetir) com link para a tela.
- Dado um documento processado, quando a pessoa pergunta sobre seu Markdown, então o copilot responde com o material persistido.
- Dado outro Workspace ou um papel sem alcance, quando a pessoa pergunta sobre esses dados, então o copilot não os revela.
- Dado que nada corresponde à pergunta, então o copilot informa que não encontrou.
- Dado um documento apagado ou substituído, então o Markdown antigo deixa de ser consultável.

## Qualidades e operação

- Segurança: a avaliar.
- Privacidade: a avaliar.
- Desempenho e volume: a avaliar.
- Auditoria e observabilidade: a avaliar.

## Dependências

- SPEC-0030 (Coleções), SPEC-0021 (assistente atual) e BACKLOG-0027 (relacionado, independente).
- Persistência nova: texto convertido e trechos (com etiquetas) por documento, confirmada no data-discovery e registrada em `.specsfy/DATABASE.md` ("Conteúdo processado do documento da coleção").

## Situações de erro

- Sem resultado relevante: informa que não encontrou.
- Falha do modelo ou da busca: mensagem genérica já usada pelo assistente, sem detalhes internos.
- Material processado ausente (documento anterior à persistência): informa a limitação.

## Escopo

- Dentro: consulta a conteúdo indexado, estado operacional e Markdown processado persistido; fontes clicáveis; seletor de coleção opcional como filtro; sugestão de passo com link.
- Fora: ações de escrita pelo copilot; memória de longo prazo (BACKLOG-0027); histórico de versões substituídas; prazo fixo de retenção.

## Dúvidas, decisões e riscos

- Decisão da pessoa em 2026-10-09: manter a evolução do copilot no backlog e continuar o desenvolvimento atual.
- Decisão (Pergunta 1, 2026-10-09): escopo de acesso = conteúdo das coleções + estado operacional + material do pipeline antes da publicação.
- Decisão (Pergunta 2): persistir o Markdown e os metadados processados no worker.
- Decisão (Pergunta 3): herdar Workspace e papel de quem pergunta.
- Decisão (Pergunta 4): sem seletor obrigatório; seletor vira filtro.
- Decisão (Pergunta 5): consulta e sugestão de ação, sem executar.
- Decisão (Pergunta 6): retenção enquanto o documento existir, uma versão.
- Decisão (Pergunta 7): fontes clicáveis em toda resposta.
- Decisão (Pergunta 8): reproduzir e corrigir o relato de coleção selecionada antes da spec, em branch `fix/`.
- Decisão (data-discovery, 2026-10-09): guardar o texto convertido e os trechos com etiquetas; o original continua só no armazenamento do envio.
- Área encerrada pelo limite de oito perguntas: Descoberta do 0038.
- Aberto: confirmar a regra de nunca expor credenciais; desempenho e volume da busca em todas as coleções; definição da interface (a especificar com os especialistas de UX/UI).
- Relato de consulta da coleção ainda sem reprodução; não atribuir sua causa somente ao prompt.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

1. Concluído: relato de coleção selecionada reproduzido e corrigido em `fix/assistente-colecao-selecionada` (commit 5d23872).
2. Concluído: data-discovery da persistência (texto convertido + trechos com etiquetas; uma versão por documento).
3. Concluído: promovido para a SPEC-0031 (Draft). Próximo: `$specsfy-04-validate`.
