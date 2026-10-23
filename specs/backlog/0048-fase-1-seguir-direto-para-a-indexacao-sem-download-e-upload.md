# Backlog: Fase 1: seguir direto para a indexação sem download e upload

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0048 |
| Status | Promoted |
| Produto | RAG Pipeline |
| Épico | Fase 1: receber, limpar, conferir e liberar para a base (M04) |
| Funcionalidade | Atalho do lote da Fase 1 para a indexação da Fase 2 |
| Tipo | Melhoria |
| Prioridade | Não priorizado |
| Milestones | M04 (extensão; a confirmar com `$specsfy-milestone-governor`) |
| Criado em | 2026-10-22 |
| Spec promovida | specs/in-progress/0043-seguir-direto-para-a-indexacao/spec.md |

## Ideia original

eu quero poder usar os documenteos em .md criados na primeira fase diretemamento ao inves de fazer download e upload novamente. ter a opção de seguir direto, mas como opção.

## Problema percebido

Hoje a pessoa baixa o pacote de .md do lote da Fase 1 e o envia de novo ao fluxo de ingestão da Fase 2; é um desvio manual sem valor agregado, que também permite subir uma versão errada ou antiga.

## Pessoa afetada ou beneficiada

Pessoa da consultoria (owner/admin) que converte, revisa e indexa os documentos de uma empresa.

## Resultado ou valor esperado

Passar do lote revisado à indexação sem sair do sistema, usando exatamente os .md revisados, mantendo o caminho atual como opção.

## Contexto

Fases já existentes: conversão em lotes (SPEC-0023, M04), fluxo de ingestão em etapas (SPEC-0026), coleções por workspace com envios acumulados (SPEC-0030) e Liberar para a base (SPEC-0039).

Estado observado em 2026-10-22: o lote de conversão expõe `GET /conversoes/{lote}/documentos/{doc}/markdown` e `GET /conversoes/{lote}/pacote` (zip); o fluxo de ingestão (`frontend/src/features/ingestao/EtapaArquivos.tsx`) recebe `.md` escolhidos no navegador, ou a "base preparada", e cria o envio por `POST /envios`. O painel do lote fica em `frontend/src/features/conversao/PainelLoteConversao.tsx`, onde hoje está o download do pacote.

## Referências relacionadas

- `specs/inbox/2026-10-22-231328-seguir-direto-da-fase-1-para-a-fase-2-sem-download-e-upload.md` (origem; não alterada).
- Spec relacionada: `specs/completed/0023-fase-1-recebimento-e-processamento-de-documentos-ate-markdown/spec.md` (lote e pacote).
- Spec relacionada: SPEC-0026 (fluxo de ingestão em etapas), SPEC-0030 (coleções por workspace com envios acumulados), `specs/completed/0039-fase-1-decisao-da-empresa-e-atualizacao/spec.md` ("Liberar para a base").
- Backlog relacionado: `specs/backlog/0043-fase-1-conferencia-e-atualizacao.md`.
- Sem duplicata encontrada.

## Comportamento esperado

Declarado nas respostas da pessoa (2026-10-22):

1. **Entrada (Pergunta 1):** no painel do lote de conversão, um botão "Seguir para a indexação" ao lado de "baixar pacote". Ele leva ao fluxo de ingestão com os `.md` do lote já selecionados.
2. **Quais documentos (Pergunta 2):** a pessoa marca no painel os documentos que quer indexar; os aptos já vêm marcados e ela pode desmarcar.
3. **Destino (Pergunta 3):** a coleção é escolhida na etapa de destino do fluxo de ingestão. Pode ser uma coleção nova ou acumular numa existente do mesmo workspace (SPEC-0030).
4. **Documento alterado (Pergunta 4):** se o `.md` muda depois de indexado (nova limpeza, decisão da empresa, reprocessamento por IA), o painel marca o documento como "alterado desde a indexação". Reindexar é ação explícita e confirmada, e o envio acumulado substitui a versão antiga.
5. **Confirmação (Pergunta 5):** antes de indexar, mostra a contagem de documentos marcados, a coleção de destino e o aviso de que a indexação gera embeddings. Não mostra estimativa de custo em valor.
6. **Disponibilidade (Perguntas 6 e 7):** o botão fica disponível quando o lote terminou (concluído ou concluído com falhas) e tem pelo menos um documento apto, sem exigir liberação. A revisão (contradições, decisão da empresa e "Liberar para a base") continua na coleção, depois da indexação, como hoje. A resposta da Pergunta 6 ("só depois de liberar") foi substituída em 2026-10-22, porque "Liberar para a base" é marca da coleção (`colecoes.revisada_em`, SPEC-0039) e só existe depois de os `.md` estarem nela.
7. **Opção, não substituição:** o upload manual de `.md` e a "base preparada" continuam como estão.

## Regras de negócio

- Declarado: o atalho é opcional; não remove nem altera o caminho de download e upload.
- Declarado: o atalho não depende de liberação; basta o lote ter terminado e ter documento apto.
- Fato observado: os arquivos do lote (original e `.md`) são apagados 7 dias após o processamento de cada documento (`expira_em`); depois disso o documento não pode mais ser indexado pelo atalho e o botão o trata como indisponível.
- Declarado: documentos aptos vêm marcados por padrão; a pessoa decide o que entra.
- Declarado: documento alterado desde a indexação nunca é reindexado sem confirmação explícita.
- Inferência (herda DEC-007 do M04): só owner e admin acionam o atalho; member consulta. A confirmar na spec.
- Inferência: "apto" segue a regra que o lote já aplica ao download (exclui o bloqueado, o com erro de conversão e o marcado "revisar" ainda não revisado). A confirmar na spec.
- Inferência: o `.md` indexado é o que está guardado no sistema no momento da confirmação, não uma cópia do navegador.

## Critérios de aceitação

- Dado um lote terminado com documentos aptos, quando a pessoa (owner ou admin) abre o painel do lote, então vê "Seguir para a indexação" com os aptos marcados e pode desmarcar qualquer um.
- Dado um lote ainda em processamento, ou sem documento apto, ou com os arquivos já expirados, quando a pessoa abre o painel, então o botão está indisponível e o painel indica o motivo.
- Dado um lote terminado, quando a pessoa confirma, então o fluxo de ingestão abre com os `.md` marcados já selecionados e pede a coleção de destino, nova ou existente do mesmo workspace.
- Dado a confirmação aberta, então ela mostra a contagem de documentos, a coleção de destino e o aviso de embeddings, e nada é indexado antes de a pessoa confirmar.
- Dado um documento indexado cujo `.md` mudou, quando a pessoa abre o painel, então o documento aparece como "alterado desde a indexação" e só é reindexado após ação explícita com confirmação.
- Dado qualquer lote, então baixar o pacote e subir `.md` manualmente continuam funcionando como antes.
- Dado um member, então o botão não aparece ou fica indisponível com o motivo, sem permitir indexar.

## Qualidades e operação

- Segurança: a autorização é verificada no servidor, não só na interface; respeita o escopo do workspace e do lote da pessoa.
- Privacidade: os `.md` não saem do sistema nem passam pelo navegador; nada do cliente entra no repositório.
- Desempenho e volume: lote típico de 10 a 50 documentos (hipótese do M04); a indexação segue o fluxo assíncrono já existente.
- Auditoria e observabilidade: o envio criado pelo atalho registra o lote de origem e a versão de cada `.md`, para explicar depois de onde veio cada chunk.

## Dependências

- SPEC-0023 (lote e `.md` da Fase 1), SPEC-0026 (fluxo de ingestão), SPEC-0030 (coleções e envios acumulados) e SPEC-0039 (liberação do lote), todas entregues.
- Provider de embeddings configurado para o workspace (já exigido pelo fluxo atual).

## Situações de erro

Inferência (seguem os padrões atuais do sistema; a confirmar na spec):

- Documento do lote removido ou alterado entre marcar e confirmar: avisa e pede nova marcação.
- Nenhum documento marcado: o botão de confirmar fica indisponível.
- Falha do provider de embeddings ou do Qdrant: tratada pelo envio existente (estado de falha e retry de `POST /envios/{id}/retry`).
- Sem permissão: mensagem clara, sem iniciar o envio.

## Escopo

- Dentro: botão no painel do lote com a regra de disponibilidade, seleção dos documentos, passagem dos `.md` do lote ao fluxo de ingestão, confirmação, marca de "alterado desde a indexação", reindexação confirmada, permissões e estados da tela.
- Fora: exigir ou criar marca de liberação no lote (a liberação continua na coleção, SPEC-0039); remover ou alterar o upload manual e a "base preparada"; estimativa de custo em valor; reindexação automática; mudar o fluxo de ingestão além de aceitar a origem "lote"; novas regras de limpeza, contradição ou decisão da empresa.

## Dúvidas, decisões e riscos

- Decisões confirmadas em 2026-10-22: Perguntas 1 a 6, na seção "Comportamento esperado".
- Conflito resolvido em 2026-10-22: Pergunta 7, opção 1 (ver "Comportamento esperado", item 6).
- Aberto, não bloqueante (suposições reversíveis da seção "Regras de negócio"): papéis, definição de "apto" e o tratamento dos erros acima.
- Risco: versão do `.md` usada na indexação divergir da exibida ao marcar; mitigado ao ler o `.md` guardado no momento da confirmação.
- Risco: custo de embeddings ao reindexar; mitigado pela confirmação explícita.
- Interface: a entrega muda tela existente (painel do lote). A spec precisa registrar telas, componentes reaproveitados (`PainelLoteConversao`, fluxo de ingestão), estados (carregando, vazio, erro, sem permissão) e teclado conforme o contrato de interface; a revisão visual vale para esta entrega.
- Dados (confirmados em 2026-10-22 via `$specsfy-data-discovery`, registrados em `.specsfy/DATABASE.md`): a origem (lote, documento do lote e versão do `.md`) permanece enquanto o documento existir na coleção; a marca "alterado desde a indexação" deixa de ser calculada quando o arquivo do lote expira (7 dias), com o aviso "arquivo do lote expirado"; owner, admin e member veem a origem e a marca, e só owner e admin reindexam.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras (permissões e erros como suposições a confirmar).
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promovido a `SPEC-0043` em 2026-10-22; a spec passa a governar o comportamento. A descoberta de dados está concluída; a descoberta de interface do painel do lote acontece na especificação.
