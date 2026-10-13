# Backlog: Fase 1: detectar e reagrupar sequências de imagens e páginas e montar tabelas

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0040 |
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

prints podem ou não ser uma sequência (conversas, passo a passo de app, slides); organizar sequências e montar tabelas em Markdown (mensagens de 2026-10-09)

## Problema percebido

Imagens e páginas soltas perdem a ordem e o agrupamento; várias conversas ou tutoriais chegam misturados, e tabelas se perdem na extração.

## Pessoa afetada ou beneficiada

Pessoa da consultoria que prepara a base de conhecimento a partir de documentos recebidos de empresas clientes

## Resultado ou valor esperado

Sequências são reconhecidas e reagrupadas de forma genérica, imagens isoladas viram documento próprio e tabelas saem como tabelas Markdown.

## Contexto

Fase 1 do rag-pipeline (PROJECT.md:6). Atualização de 2026-10-13: a SPEC-0023 (mergeada na `main`, #22) já converte PDF, PPT/PPTX, DOC/DOCX, XLS/XLSX e imagem (OCR) em `.md`, um por arquivo; o agrupamento de imagens e a junção de tabelas ficam para este item. Capturas: specs/inbox/2026-10-09-192547-*.md e 2026-10-09-194532-*.md. Entradas variam: PDF (inclusive prints de PPT/PPTX e fotos), Google Docs/Planilhas, XLS, imagens JPG/PNG (conversas, apresentações, telas de app; podem ou não ser sequência), URLs. Áreas: comercial, atendimento, RH, marketing, diretoria. Saída: .md limpos, sem contradições nem duplicidade, prontos para a Fase 2. Contrato do .md: SPEC-0002. Dividido em 5 backlogs por decisão do usuário em 2026-10-09 (Pergunta 1, opção 1).

## Referências relacionadas

- `specs/inbox/2026-10-09-192547-receber-documentos-em-varios-formatos-e-extrair-informacoes-para-gerar-os-markdown-de-processamento.md` — origem (captura).
- `specs/inbox/2026-10-09-194532-fase-1-receber-documentos-extrair-o-conteudo-de-dominio-gerar-markdown-e-relatar-contradicoes.md` — origem (captura detalhada).
- `specs/completed/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/spec.md` — spec relacionada: contrato do Markdown de saída.
- `specs/completed/0030-colecoes-por-workspace-com-envios-acumulados/spec.md` — spec relacionada: envio atual, só `.md`.
- `PROJECT.md` (linhas 6 e 166) — documentação: Fase 1 fora do componente atual.
- Backlogs irmãos da Fase 1: 0039 a 0043 (dividido em 5 por decisão do usuário em 2026-10-09).

## Comportamento esperado

- Reconhecer imagens que formam sequência (conversa, tutorial em telas, slides fotografados) e produzir um `.md` único por grupo (declaração do usuário; briefing.md do projeto-mãe v. 2026-07-29, colado na conversa de 2026-10-09).
- Tratar imagem isolada como documento próprio; sequências são apenas um caso possível (esclarecimento do usuário, 2026-10-09).
- Montar tabelas como tabelas Markdown.
- **Misturadas (Pergunta 1, 2026-10-13, opção 1):** quando as imagens chegam misturadas, o sistema propõe os grupos e a ordem; a pessoa ajusta e aprova antes de gerar os `.md`. Nada é separado ou reordenado sem aprovação.
- **Pistas da sugestão (Pergunta 2, opção 3):** a primeira entrega usa só nome do arquivo, data e hora e pasta de origem. A leitura do conteúdo pelo OCR (nome do contato, horários, numeração de slide) fica como evolução, depois de medir os acertos com prints reais.
- **Tela de aprovação (Pergunta 7, opção 3):** aparece em todo envio com várias imagens. Quando o sistema tem certeza, vem tudo pré-aprovado e basta um clique em "confirmar".
- **Tabelas (Pergunta 3, opção 3):** tabela simples vira tabela Markdown. Tabela complexa (células mescladas, aninhadas, cabeçalho de vários níveis) vira texto corrido, uma frase por linha, e o documento é marcado "revisar".
- **Tabela que continua na página seguinte (Pergunta 4, opção 1):** é juntada numa só, sem o cabeçalho repetido, quando as colunas batem. Em caso de dúvida, não junta e marca "revisar".
- **Origem no `.md` (Pergunta 5, opção 1):** uma seção por imagem, na ordem aprovada, com marcador "Origem: <arquivo>". Sujeito à conferência com o contrato da SPEC-0002 antes da spec.
- **Imagem ilegível (Pergunta 6, opção 1):** o grupo é gerado com o aviso "imagem não legível: <arquivo>" no lugar da imagem; o documento é marcado "revisar" e o relatório do lote lista o arquivo.
- **PDF (Pergunta 8, opção 1):** um PDF gera um `.md`. A divisão por assunto é tratada no 0041. Dividir PDF de páginas-imagem com a tela de aprovação fica como evolução.

## Regras de negócio

- Briefing: o cliente isola a sequência em pasta própria, com nomes já em ordem sequencial; ordem por nome + EXIF + confirmação manual.
- Confirmação manual da ordem das imagens quando houver incerteza; nunca reordenar silenciosamente.
- Reordenação totalmente automática fica fora da V1 do briefing.

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado.

## Qualidades e operação

- Segurança: a avaliar.
- Privacidade: a avaliar.
- Desempenho e volume: a avaliar.
- Auditoria e observabilidade: a avaliar.

## Dependências

- SPEC-0023 (conversão, já na `main`) e backlog 0039 (HTML/URL, limites, marca "revisar" no relatório do lote).

## Situações de erro

- A esclarecer.

## Escopo

- Dentro: detectar/agrupar sequências, ordenar com confirmação, montar tabelas.
- Fora: OCR/conversão em si (0039); limpeza (0041).

## Dúvidas, decisões e riscos

- Resolvido (Pergunta 1): o briefing (pasta isolada) e a mensagem do usuário (10 a 20 prints com três conversas misturadas) se conciliam assim: o sistema propõe a separação e a pessoa aprova.
- Em aberto: critério para detectar o limite entre duas sequências usando só nome, data e pasta; formato exato do marcador de origem (conferir SPEC-0002); critério de "tabela complexa" e de "colunas batem".
- Marco: a Fase 1 terá marco novo entre o M02 e o deploy (decisão do 0039, Pergunta 8).
- Área de perguntas do 0040 encerrada no limite de oito perguntas (2026-10-13).
- Dependência: a tela de aprovação reutiliza a aba "Conversão de documentos" (SPEC-0023).

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
