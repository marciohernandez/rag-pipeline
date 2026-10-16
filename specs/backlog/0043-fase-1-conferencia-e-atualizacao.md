# Backlog: Fase 1: registrar a decisão da empresa e atualizar os Markdown para a Fase 2

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0043 |
| Status | Ready for specification |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | M04 |
| Criado em | 2026-10-09 |
| Spec promovida | Nenhuma |

## Ideia original

após conferir com a empresa o que está valendo, atualizar os .md e deixá-los prontos para a segunda parte (mensagens de 2026-10-09)

## Problema percebido

Sem um passo que traga a decisão da empresa de volta, os .md continuam contraditórios e a Fase 2 indexaria informação não validada.

## Pessoa afetada ou beneficiada

Pessoa da consultoria que prepara a base de conhecimento a partir de documentos recebidos de empresas clientes

## Resultado ou valor esperado

A decisão sobre cada contradição é registrada e os .md são atualizados, liberando a entrega à Fase 2.

## Contexto

Fase 1 do rag-pipeline (PROJECT.md:6). Atualização de 2026-10-13: a conversão (SPEC-0023) já está na `main`; este item registra a decisão da empresa sobre as contradições do 0042 e corrige os `.md`. Capturas: specs/inbox/2026-10-09-192547-*.md e 2026-10-09-194532-*.md. Entradas variam: PDF (inclusive prints de PPT/PPTX e fotos), Google Docs/Planilhas, XLS, imagens JPG/PNG (conversas, apresentações, telas de app; podem ou não ser sequência), URLs. Áreas: comercial, atendimento, RH, marketing, diretoria. Saída: .md limpos, sem contradições nem duplicidade, prontos para a Fase 2. Contrato do .md: SPEC-0002. Dividido em 5 backlogs por decisão do usuário em 2026-10-09 (Pergunta 1, opção 1).

## Referências relacionadas

- `specs/inbox/2026-10-09-192547-receber-documentos-em-varios-formatos-e-extrair-informacoes-para-gerar-os-markdown-de-processamento.md` — origem (captura).
- `specs/inbox/2026-10-09-194532-fase-1-receber-documentos-extrair-o-conteudo-de-dominio-gerar-markdown-e-relatar-contradicoes.md` — origem (captura detalhada).
- `specs/completed/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/spec.md` — spec relacionada: contrato do Markdown de saída.
- `specs/completed/0030-colecoes-por-workspace-com-envios-acumulados/spec.md` — spec relacionada: envio atual, só `.md`.
- `PROJECT.md` (linhas 6 e 166) — documentação: Fase 1 fora do componente atual.
- Backlogs irmãos da Fase 1: 0039 a 0043 (dividido em 5 por decisão do usuário em 2026-10-09).

## Comportamento esperado

- O relatório vai à empresa (dona da informação), que responde em formato livre; um agente de IA interpreta e mapeia a resposta às contradições (declaração do usuário; briefing.md do projeto-mãe v. 2026-07-29, colado na conversa de 2026-10-09).
- Nenhuma correção é gravada sem confirmação humana explícita da consultoria.
- Aplicar a correção confirmada, rodar nova análise e repetir até não haver contradições.
- **Entrada da resposta (Pergunta 1, 2026-10-13, opção 1):** a pessoa cola o texto da resposta da empresa numa caixa ligada ao relatório; a IA interpreta e propõe, para cada contradição, qual versão vale. Anexos ficam para depois.
- **Conferência (Pergunta 2, opção 3):** a IA marca cada proposta como "clara" ou "incerta"; as claras vêm pré-aprovadas num bloco e as incertas pedem decisão individual. Nada muda no `.md` sem confirmação.
- **Correção (Pergunta 3, opção 1):** o trecho que não vale é corrigido no próprio `.md` (sai o valor errado, entra o certo).
- **Histórico (Pergunta 4, opção 1):** cada correção cria uma versão nova do `.md`, com a anterior preservada, e um registro de decisões (quem confirmou, quando, qual contradição e qual resposta da empresa a justificou). A pessoa pode voltar a uma versão antiga.
- **Novo ciclo (Pergunta 5, opção 1):** cada reanálise é um clique em "Analisar contradições"; o sistema mostra o que foi resolvido e o que apareceu de novo desde a rodada anterior.
- **Pronto para a Fase 2 (Pergunta 6, opção 1):** a pessoa marca a coleção como "revisada" por um botão "Liberar para a base". Pode liberar com contradições abertas, com aviso explícito.
- **Permissões (Pergunta 7, opção 3):** quem edita o Workspace confirma as correções; só quem administra libera a coleção. Conferir os papéis existentes antes da spec.
- **Meta (Pergunta 8, opção 1):** pelo menos 70% dos `.md` finais validados sem edição manual depois do primeiro ciclo, medido nos documentos do gabarito do 0041.

## Regras de negócio

- Checkpoint humano obrigatório antes de qualquer escrita no `.md`.
- A conferência com a empresa acontece fora do sistema.

## Critérios de aceitação

Derivados das decisões confirmadas (Perguntas 1 a 8 e Interface), a validar na spec:

- Dado o relatório de contradições e o texto da resposta da empresa colado, quando owner ou admin clica em "Interpretar resposta", então cada contradição recebe uma proposta marcada "clara" ou "incerta".
- Dado propostas "claras", quando a pessoa confirma o bloco, então cada trecho é corrigido no próprio `.md`, nasce uma versão nova com a anterior preservada e o registro mostra quem confirmou, quando, a contradição e a resposta da empresa que a justificou.
- Dado uma proposta "incerta", quando a pessoa não decide, então nada muda no `.md`.
- Dado uma contradição não coberta pela resposta, quando a rodada termina, então ela fica "Sem decisão" e continua aberta.
- Dado uma correção aplicada, quando a pessoa clica em "Analisar contradições", então o sistema mostra o que foi resolvido e o que apareceu de novo desde a rodada anterior.
- Dado uma coleção com contradições abertas, quando owner ou admin clica em "Liberar para a base", então o `Dialog` avisa a contagem de abertas e só libera após a confirmação explícita.
- Dado um member, quando abre a rota, então consulta, mas não interpreta, não confirma e não libera.
- Dado o gabarito do 0041, quando o ciclo roda, então pelo menos 70% dos `.md` finais passam sem edição manual (medido após a entrega do gabarito).

## Qualidades e operação

- Segurança: só owner e admin interpretam, confirmam e liberam; a chave de IA nunca é devolvida nem registrada em log; checkpoint humano antes de qualquer escrita.
- Privacidade: o texto da resposta da empresa vai à IA externa só após o clique e com aviso, e depende da chave de IA por Workspace (SPEC-0037); decisões ficam enquanto a coleção existir e versões antigas por 90 dias (DATABASE.md); ao apagar a coleção sobra só um registro mínimo.
- Desempenho e volume: a interpretação roda em segundo plano para respostas longas e mostra progresso; limites de tamanho da resposta a definir na spec.
- Auditoria e observabilidade: registro de decisões com autor, data, contradição, resposta e versão do `.md`.

## Dependências

- Backlog 0042 (relatório de contradições), 0041 (chave de IA por Workspace e gabarito), SPEC-0030 (coleções) e Fase 2 já entregue (envio à base vetorial).

## Situações de erro

- Sem chave de IA: avisa e não interpreta; a pessoa pode decidir cada contradição à mão.
- IA indisponível ou resposta inválida: nada é gravado; a pessoa tenta de novo.
- Resposta da empresa que não cobre uma contradição: ela fica "Sem decisão" e continua aberta.
- Trecho não localizado: proposta "incerta", edição manual e confirmação.
- Coleção já liberada e corrigida depois: precisa de novo envio à Fase 2 (a detalhar na spec).

## Escopo

- Dentro: registro da decisão, confirmação humana, aplicação da correção e novo ciclo.
- Fora: a detecção em si (0042).

## Dúvidas, decisões e riscos

- Resolvido: entrada da resposta (Pergunta 1), versionamento e histórico (Pergunta 4) e meta de 70% (Pergunta 8).
- Resolvido: resposta que não cobre tudo fica "sem decisão" e aberta. Em aberto, a decidir na spec como suposição reversível: como a IA localiza o trecho exato a corrigir no `.md`; como ficam os trechos já enviados à base vetorial se a coleção for corrigida depois de liberada (reenvio da Fase 2).
- Permissões (conferência dos papéis existentes, 2026-10-16): o sistema só tem `owner`, `admin` e `member`; "quem edita" e "quem administra" (Pergunta 7) coincidem em owner e admin (papel de escrita), e member só consulta. Aplicação da DEC-007 da SPEC-0037, reversível se a pessoa pedir um papel novo em outra spec.
- Interface (2026-10-16), Pergunta 1, opção 1: na rota do relatório de contradições (`/workspaces/{id}/colecoes/{colecaoId}/contradicoes`) há uma caixa "Resposta da empresa" no topo com o botão "Interpretar resposta". Cada cartão ganha a proposta da IA marcada "clara" ou "incerta"; as claras ficam num bloco pré-aprovado com "Confirmar todas" e as incertas pedem decisão individual (Aceitar, Editar ou Manter sem decisão). Reaproveita os cartões da BACKLOG-0042.
- Interface (2026-10-16), Pergunta 2, opção 1: cada cartão confirmado mostra "Corrigido" com a versão do `.md` e o link "Ver versões"; ao fim da rodada um resumo diz o que foi resolvido e o que apareceu de novo. No cabeçalho da rota ficam "Analisar contradições" e "Liberar para a base"; liberar com contradições abertas abre um `Dialog` com aviso explícito e a contagem de abertas. O histórico de versões e a volta a uma versão antiga ficam no detalhe do documento, com confirmação.
- Interface (2026-10-16), Pergunta 3, opção 1: a contradição sem resposta da empresa fica "Sem decisão" e continua aberta, destacada como pendente. Se a IA não localiza o trecho exato, a proposta vira "incerta" com a mensagem "Não foi possível localizar o trecho; indique qual corrigir", e a pessoa edita o texto da correção à mão antes de confirmar. Nada é gravado sem a confirmação.
- Área Interface do 0043 concluída em 2026-10-16 (três perguntas); acessibilidade e teclado seguem o `DESIGNSYSTEM.MD`.
- Risco: a IA reescrever mais do que a correção pedida; mitigado pela conferência humana e pelo histórico.
- Risco de privacidade: o texto da resposta da empresa vai à IA externa; depende da chave de IA por Workspace (0041).
- Área de perguntas do 0043 encerrada no limite de oito perguntas (2026-10-13).

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

`$specsfy-03-specify` depois da SPEC-0037 e da 0042. Pendente herdado: gabarito do 0041.
