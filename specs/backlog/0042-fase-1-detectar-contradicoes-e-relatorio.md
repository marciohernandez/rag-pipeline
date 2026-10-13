# Backlog: Fase 1: detectar contradições entre documentos e gerar relatório com origem

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0042 |
| Status | Refining |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-09 |
| Spec promovida | Nenhuma |

## Ideia original

analisar todos os .md, achar informações contraditórias e gerar relatório com os arquivos de origem para conferir com a empresa (mensagens de 2026-10-09)

## Problema percebido

Áreas diferentes da mesma empresa dão informações conflitantes (ex.: cancelamento 7 dias no comercial e 15 no marketing; preços e descontos) e o RAG responderia de forma incoerente.

## Pessoa afetada ou beneficiada

Pessoa da consultoria que prepara a base de conhecimento a partir de documentos recebidos de empresas clientes

## Resultado ou valor esperado

Relatório das contradições, cada uma com os arquivos e trechos de origem, para a empresa decidir o que vale.

## Contexto

Fase 1 do rag-pipeline (PROJECT.md:6). Atualização de 2026-10-13: a conversão (SPEC-0023) já está na `main`; este item analisa os `.md` da coleção, não converte. Capturas: specs/inbox/2026-10-09-192547-*.md e 2026-10-09-194532-*.md. Entradas variam: PDF (inclusive prints de PPT/PPTX e fotos), Google Docs/Planilhas, XLS, imagens JPG/PNG (conversas, apresentações, telas de app; podem ou não ser sequência), URLs. Áreas: comercial, atendimento, RH, marketing, diretoria. Saída: .md limpos, sem contradições nem duplicidade, prontos para a Fase 2. Contrato do .md: SPEC-0002. Dividido em 5 backlogs por decisão do usuário em 2026-10-09 (Pergunta 1, opção 1).

## Referências relacionadas

- `specs/inbox/2026-10-09-192547-receber-documentos-em-varios-formatos-e-extrair-informacoes-para-gerar-os-markdown-de-processamento.md` — origem (captura).
- `specs/inbox/2026-10-09-194532-fase-1-receber-documentos-extrair-o-conteudo-de-dominio-gerar-markdown-e-relatar-contradicoes.md` — origem (captura detalhada).
- `specs/completed/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/spec.md` — spec relacionada: contrato do Markdown de saída.
- `specs/completed/0030-colecoes-por-workspace-com-envios-acumulados/spec.md` — spec relacionada: envio atual, só `.md`.
- `PROJECT.md` (linhas 6 e 166) — documentação: Fase 1 fora do componente atual.
- Backlogs irmãos da Fase 1: 0039 a 0043 (dividido em 5 por decisão do usuário em 2026-10-09).

## Comportamento esperado

- Comparar os `.md` entre si e detectar contradições e duplicidade (declaração do usuário; briefing.md do projeto-mãe v. 2026-07-29, colado na conversa de 2026-10-09).
- Gerar relatório `.md` baixável com os documentos em conflito e a divergência exata, com arquivos e trechos de origem.
- Exemplo do usuário: política de cancelamento de 7 dias no comercial e 15 no marketing; preços e descontos.
- **Como detecta (Pergunta 1, 2026-10-13, opção 1):** agrupa os trechos por assunto e a IA julga só os pares do mesmo assunto, usando a chave de IA do Workspace.
- **Quando roda (Pergunta 2, opção 1):** só quando a pessoa clica em "Analisar contradições", com aviso de que o conteúdo será enviado à IA configurada.
- **Entre quais documentos (Pergunta 3, opção 1):** todos os `.md` da coleção, o que já estava e o que chegou agora.
- **O que conta (Pergunta 4, opção 3):** conflito direto, diferença de versão e duplicidade. Etiquetas: "conflito", "versão desatualizada" e "duplicado".
- **Relatório (Pergunta 5, opção 3):** um cartão por ocorrência, com assunto, etiqueta, trechos lado a lado, arquivo de origem (e imagem, quando vier de print) e explicação da divergência; organizado por assunto, com as de maior impacto (valores, prazos) no topo.
- **Formato (Pergunta 6, opção 3):** tela no sistema, com download em `.md` e em PDF.
- **Meta de qualidade (Pergunta 7, opção 1):** capturar pelo menos 90% das contradições reais, medido contra a amostra do gabarito do 0041 revisada por uma pessoa.
- **Falhas (Pergunta 8, opção 1):** sem chave de IA, avisa e não começa; se a análise cair no meio, guarda o que foi analisado e retoma de onde parou; coleção grande é processada em partes; o que já foi analisado aparece enquanto o resto continua, com aviso claro de que a análise não terminou.

## Regras de negócio

- O relatório serve para conferir com a empresa o que vale; não corrige nada sozinho.

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado.

## Qualidades e operação

- Segurança: a avaliar.
- Privacidade: a avaliar.
- Desempenho e volume: a avaliar.
- Auditoria e observabilidade: a avaliar.

## Dependências

- SPEC-0023 (conversão), backlogs 0039 e 0040 (origem por arquivo e por imagem, marca "revisar"), 0041 (chave de IA por Workspace e gabarito para medir os 90%) e 0043 (decisão da empresa).

## Situações de erro

- A esclarecer.

## Escopo

- Dentro: análise cruzada e relatório.
- Fora: aplicar correções (0043).

## Dúvidas, decisões e riscos

- Resolvido: critério de contradição (Pergunta 4), meta de 90% (Pergunta 7) e escala (agrupa por assunto antes de a IA julgar, Pergunta 1).
- Em aberto: como agrupar por assunto (o que usa para aproximar os trechos), custo estimado por coleção, tamanho de coleção a partir do qual processa em partes.
- Risco: falso alarme enche o relatório; contradição perdida passa para a base. A decisão final é sempre da empresa.
- Risco de privacidade: o conteúdo dos documentos vai à IA externa; depende da chave de IA por Workspace (a definir no 0041).
- Área de perguntas do 0042 encerrada no limite de oito perguntas (2026-10-13).

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
