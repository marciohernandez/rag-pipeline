# Backlog: Fase 1: extrair só o conteúdo de domínio e limpar ruído e duplicidade

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0041 |
| Status | Promoted |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | M04 |
| Criado em | 2026-10-09 |
| Spec promovida | specs/draft/0037-fase-1-conteudo-de-dominio-e-limpeza/spec.md |

## Ideia original

extrair as informações de domínio, não números de página ou HTML; entregar documentos limpos, sem duplicidade (mensagens de 2026-10-09)

## Problema percebido

A extração traz acessórios (numeração, HTML, repetições) e informação duplicada que vira ruído e duplicidade na base vetorial.

## Pessoa afetada ou beneficiada

Pessoa da consultoria que prepara a base de conhecimento a partir de documentos recebidos de empresas clientes

## Resultado ou valor esperado

Markdown só com informação do core business, sem acessórios e sem duplicidade.

## Contexto

Fase 1 do rag-pipeline (PROJECT.md:6). Atualização de 2026-10-13: a conversão (SPEC-0023) já está na `main`; este item limpa o Markdown que ela gera. Capturas: specs/inbox/2026-10-09-192547-*.md e 2026-10-09-194532-*.md. Entradas variam: PDF (inclusive prints de PPT/PPTX e fotos), Google Docs/Planilhas, XLS, imagens JPG/PNG (conversas, apresentações, telas de app; podem ou não ser sequência), URLs. Áreas: comercial, atendimento, RH, marketing, diretoria. Saída: .md limpos, sem contradições nem duplicidade, prontos para a Fase 2. Contrato do .md: SPEC-0002. Dividido em 5 backlogs por decisão do usuário em 2026-10-09 (Pergunta 1, opção 1).

## Referências relacionadas

- `specs/inbox/2026-10-09-192547-receber-documentos-em-varios-formatos-e-extrair-informacoes-para-gerar-os-markdown-de-processamento.md` — origem (captura).
- `specs/inbox/2026-10-09-194532-fase-1-receber-documentos-extrair-o-conteudo-de-dominio-gerar-markdown-e-relatar-contradicoes.md` — origem (captura detalhada).
- `specs/completed/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/spec.md` — spec relacionada: contrato do Markdown de saída.
- `specs/completed/0030-colecoes-por-workspace-com-envios-acumulados/spec.md` — spec relacionada: envio atual, só `.md`.
- `PROJECT.md` (linhas 6 e 166) — documentação: Fase 1 fora do componente atual.
- `specs/backlog/0044-fase-1-expandir-variacoes-de-perguntas-em-documentos-qa.md` — backlog relacionado: Q&A separado deste item.
- Backlogs irmãos da Fase 1: 0039 a 0043 (dividido em 5 por decisão do usuário em 2026-10-09).

## Comportamento esperado

- Filtro de Domínio em três camadas, decisão da pessoa (Pergunta 1, 2026-10-12): (1) regras fixas removem o ruído óbvio (número de página, rodapé repetido, menu, banner de cookie, saudação social); (2) uma IA avalia cada seção restante quanto à relevância para o domínio da empresa e atribui um grau de confiança; (3) seção de baixa confiança é mantida e marcada para conferência. Nada é descartado em silêncio.
- Domínio da empresa (Pergunta 5): a IA lê uma amostra dos documentos do lote e propõe um resumo do domínio; a pessoa confirma ou corrige antes da limpeza; o resumo aprovado fica guardado no Workspace e é reaproveitado nos lotes seguintes, com possibilidade de reajuste.
- Duplicidade (Pergunta 3): repetição exata ou quase exata é removida sozinha, mantendo uma cópia e registrando as origens das demais; informação apenas parecida (outras palavras) não é removida sozinha, e fica registrada no relatório para decisão humana (inferência da recomendação de combinar com marcação, a confirmar).
- Conferência (Pergunta 4): um relatório do lote lista exclusões e dúvidas e é baixado junto dos `.md`; as seções duvidosas ficam mantidas e a conferência acontece fora do sistema nesta primeira versão.
- Toda exclusão é registrada em log auditável.

## Regras de negócio

- Em dúvida sobre relevância, o conteúdo é mantido; perder informação real é pior que manter algum ruído.
- Nenhuma decisão automática de baixa confiança descarta informação silenciosamente.
- Sem duplicidade exata: informação repetida entre documentos é tratada (usuário, 2026-10-09), mantendo uma cópia e as origens.
- Privacidade (Pergunta 7): cada Workspace tem uma chave "permitir análise por IA externa". Desligada, só as regras fixas rodam, sem enviar texto a uma IA externa. O relatório do lote registra se a IA foi usada e qual provedor.

## Critérios de aceitação

- Dado um documento com rodapé, número de página e informação do negócio, quando o lote é processado, então o ruído óbvio sai e toda a informação do negócio permanece, e cada exclusão aparece no log.
- Dado um trecho em que a IA tem baixa confiança sobre ser ruído, quando o lote termina, então o trecho está mantido e listado no relatório como dúvida.
- Dado o mesmo parágrafo em dois documentos, quando o lote é processado, então uma cópia permanece e o relatório indica os dois arquivos de origem.
- Dado um Workspace com a chave de IA externa desligada, quando o lote é processado, então nenhum texto é enviado à IA e só as regras fixas são aplicadas.
- Dado um lote novo em um Workspace sem resumo de domínio, quando o processamento começa, então o sistema propõe o resumo e aguarda a confirmação antes de limpar.
- Dado o conjunto de gabarito da pessoa (3 ou 4 documentos reais, com o que deve ficar e o que deve sair), quando a limpeza roda, então nenhum trecho marcado como "deve ficar" é removido e a maior parte do ruído marcado é removida.

## Qualidades e operação

- Segurança: gabarito e documentos de clientes ficam fora do repositório de código; só o resumo do domínio aprovado e os logs são guardados no sistema.
- Privacidade: chave por Workspace para IA externa (decisão da Pergunta 7); relatório registra provedor; sem segredos nos logs.
- Desempenho e volume: lote típico de dezenas de documentos (10 a 50), alguns longos (Pergunta 8); processamento em segundo plano com progresso, como nos lotes de conversão atuais; custo de IA limitado pelas regras fixas aplicadas antes.
- Auditoria e observabilidade: log de toda exclusão e relatório do lote com exclusões, dúvidas e duplicidades.

## Dependências

- 0039 (conversão e formatos): entrega o Markdown que este item limpa. SPEC-0023 (conversão, PR #22) como base.
- SPEC-0002 (contrato Markdown) e SPEC-0030 (Workspaces/Coleções).
- 0042 (contradições) consome a saída deste item.
- Persistência nova (resumo do domínio por Workspace, chave de IA externa, log de exclusões e relatório do lote): passar por `$specsfy-data-discovery`.

## Situações de erro

- IA indisponível ou chave desligada: o lote segue só com regras fixas e o relatório informa que a etapa de IA não rodou.
- Resumo de domínio não confirmado: a limpeza não começa.
- Falha no meio do lote: documentos já limpos permanecem; retomar sem refazer os concluídos (a detalhar na spec).

## Escopo

- Dentro: filtro de domínio auditável (regras + IA com confiança + conferência humana), limpeza de ruído e duplicidade.
- Fora: detecção de contradições (0042); Q&A e expansão de perguntas (0044).

## Dúvidas, decisões e riscos

- Decisão (Pergunta 1, 2026-10-12): filtro em três camadas, regras fixas, IA com confiança e conteúdo de baixa confiança mantido e marcado.
- Decisão (Pergunta 2): Q&A e expansão de perguntas viram o BACKLOG-0044.
- Decisão (Pergunta 3): duplicidade exata ou quase exata removida sozinha, mantendo uma cópia e as origens.
- Decisão (Pergunta 4): conferência por relatório baixado junto do lote, sem tela nova na primeira versão.
- Decisão (Pergunta 5): a IA propõe o domínio pelos documentos, a pessoa aprova, e o resumo fica no Workspace.
- Decisão (Pergunta 6): gabarito com documentos reais da pessoa (3 ou 4), fora do repositório.
- Decisão (Pergunta 7): chave "permitir análise por IA externa" por Workspace.
- Decisão (Pergunta 8): lote típico de dezenas de documentos.
- Área encerrada pelo limite de oito perguntas: descoberta do 0041.
- Descoberta de dados concluída em 2026-10-13 (oito perguntas), registrada em `.specsfy/DATABASE.md`: (1) a IA vem de uma conexão nova do tipo "IA para análise de documentos" no cadastro de Conexões, escolhida por Workspace, com o interruptor de IA externa; (2) resumo do domínio vigente com histórico de versões, e o relatório do lote cita a versão usada; (3) log de exclusões com o trecho completo por 30 dias e depois só motivo, arquivo e posição; (4) relatórios do lote e de contradições guardados por 90 dias; (5) registro de decisões enquanto a coleção existir, versões antigas do `.md` por 90 dias; (6) quem edita vê relatórios e decisões, só quem administra vê o texto removido e o histórico do domínio; (7) ao apagar a coleção, apaga o conteúdo e fica só um registro mínimo; (8) situação e contagem de pendências por documento na tela da coleção.
- Interface (2026-10-16, exceção do M04 registrada em `specs/milestones/M04.md`), Pergunta 1, opção 3: o resumo do domínio é confirmado ou corrigido num passo dentro do lote de conversão (`ConversaoSheet`), antes de a limpeza rodar, e o resumo vigente também é consultável e editável numa seção "Domínio da empresa" em `/workspaces/[id]`, reusando um único componente. Stack observada: Next.js/React com shadcn/ui (`Sheet`, `Dialog`), `features/conversao`, `features/workspaces`, `features/conexoes`.
- Interface (2026-10-16), Pergunta 2, opção 1: o resultado da limpeza aparece no painel do lote (`PainelLoteConversao`), com a contagem de exclusões e de dúvidas ao lado de cada documento e o botão "Baixar relatório do lote", que entrega o relatório junto dos `.md`. Não cria tela nova.
- Interface (2026-10-16), Pergunta 3, opção 1: a conexão de IA para análise e a chave "permitir análise por IA externa" são configuradas na seção "Domínio da empresa" de `/workspaces/[id]`, com seletor das conexões ativas do tipo novo, interruptor da chave e atalho "Cadastrar conexão" que abre `ConexaoFormSheet` sem sair da página (padrão de `EtapaPublicacao`). Só owner e admin alteram.
- Interface (2026-10-16), Pergunta 4, opção 1: um aviso no topo do painel do lote diz o motivo e o efeito. Com a IA fora (chave desligada, sem conexão de IA ou IA indisponível), o lote segue só com as regras fixas e o relatório registra "etapa de IA não rodou". Com o resumo do domínio não confirmado, a limpeza não começa e o botão "Confirmar domínio" aparece em destaque. Cada aviso leva por link à seção "Domínio da empresa" do Workspace.
- Interface (2026-10-16), Pergunta 5, opção 2: owner e admin editam a seção "Domínio da empresa", mudam a chave e a conexão de IA e veem o texto removido e o histórico do domínio. O editor roda o lote, confirma ou corrige o resumo do domínio durante o lote, vê contagens e dúvidas e baixa o relatório (sem o texto removido). O member só consulta o resumo vigente.
- Interface (2026-10-16), Pergunta 6, opção 3: cada documento ganha situação própria ("Aguardando limpeza", "Limpando", "Limpo", "Limpo com dúvidas", "Falhou"), no padrão de `situacao.ts`, e o lote mostra o progresso total. Se um documento falha, os já limpos permanecem e o motivo aparece ao lado dele (por exemplo "IA indisponível" ou "arquivo ilegível"); o painel oferece "Tentar de novo" só para os que falharam, sem refazer os concluídos, e a opção de seguir só com as regras fixas.
- Interface (2026-10-16), Pergunta 7, opção 1: no celular a seção "Domínio da empresa" vira coluna única, com o resumo em área de texto de largura total e as ações "Salvar" e "Cadastrar conexão" empilhadas; o aviso do painel do lote fica fixo no topo e "Confirmar domínio" ocupa a largura toda; textos longos quebram sem rolagem horizontal. Reusa os padrões de `Sheet` e `DataGrid` existentes. Teclado e acessibilidade seguem o padrão do `DESIGNSYSTEM.MD` (foco visível, nomes acessíveis, `role=status` para avisos), sem pergunta própria.
- Duplicidade (2026-10-16), Pergunta 9, opção 2: "quase exata" é igualdade após normalização (maiúsculas, espaços, pontuação, acentos) mais semelhança textual de pelo menos 95% entre parágrafos ou seções com no mínimo 200 caracteres. Abaixo desse tamanho só a igualdade normalizada remove. O limite fica em configuração e é calibrado com os documentos de gabarito; o que não atinge o critério vai ao relatório para decisão humana.
- Aberto: a pessoa entregar os documentos de gabarito; ordem entre limpeza e contradições (briefing põe a análise cruzada depois da normalização, tratada como suposição); onde ficam guardados o log e o relatório.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

1. (Feito em 2026-10-13) `$specsfy-data-discovery` para o resumo do domínio, a chave por Workspace, o log de exclusões e o relatório.
2. A pessoa entregar os documentos de gabarito.
3. (Feito em 2026-10-16) Critério de "quase exata" definido na Pergunta 9.
4. `$specsfy-03-specify`, com a ordem entre limpeza e contradições e o gabarito como `Pendente`.
